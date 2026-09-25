
import AppKit
import CoreGraphics
import Foundation
import Rev28Core
import ScreenCaptureKit

// W2 harness calibration driver (plan §SYNTHETIC_HARNESS_CALIBRATION_PLAN
// items 1-9). Every OS observation becomes a structured evidence record with
// SHA-256; frozen artifacts are mandatory review inputs and are written
// append-only to both the run's frozen/ dir and the canonical
// evidence/<task>/harness/frozen/ path.

struct CalibrationOptions {
    let evidenceBase: URL
    let binaryDirectory: URL
    let items: Set<Int>
    /// Partial-run guard: when set, only the first N capture-matrix cells are
    /// exercised (the frozen rule book is then PARTIAL, never complete).
    let maxCells: Int?
}

struct ItemResult: Codable {
    let item: Int
    let name: String
    let verdict: String
    let detail: String
    let evidencePath: String
    let evidenceSHA256: String
}

struct FrozenArtifact: Codable {
    let name: String
    let path: String
    let sha256: String
}

struct CalibrationSummary: Codable {
    let taskID: String
    let runID: String
    let startedAtISO8601: String
    let finishedAtISO8601: String
    let driverExecutable: String
    let driverPID: Int32
    let harnessExecutable: String
    let harnessPID: Int32
    let occluderPID: Int32
    let sdkPath: String
    let swiftVersion: String
    let hostOSVersion: String
    let axTrusted: Bool
    let screenCaptureTrusted: Bool
    let postEventTrusted: Bool
    let screenHeightPt: Double
    let backingScaleFactor: Double
    let items: [ItemResult]
    let frozen: [FrozenArtifact]
    let verdict: String
    let notes: [String]
}

// MARK: - Item record types

struct OriginProbe: Codable {
    let markerFound: Bool
    let expectedMarkerScreenPt: [Double]
    let foundMarkerPixel: [Double]?
    let measuredOriginOffsetXPt: Double?
    let measuredOriginOffsetYPt: Double?
}

struct CaptureCellSample: Codable {
    let settled: Bool
    let requestedActivated: Bool
    let observedActivated: Bool
    let shadowsOn: Bool
    let ignoreShadows: Bool
    let includeChildWindows: Bool
    let stateKey: String
    let attempt: Int
    let expectedBBoxPt: [Double]
    let imageWidthPx: Int
    let imageHeightPx: Int
    let scale: Double
    let backingScaleFactor: Double
    let perSideDeltaPt: [String: Double]
    let measuredMaxPerSideDeltaPt: Double
    let noRuleValidity: String?
    let noRuleViolations: [String]
    let originProbe: OriginProbe?
    let capturedAtISO8601: String
}

struct CaptureCell: Codable {
    let settled: Bool
    let requestedActivated: Bool
    let observedActivated: Bool
    let shadowsOn: Bool
    let ignoreShadows: Bool
    let includeChildWindows: Bool
    let stateKey: String
    let samples: [CaptureCellSample]
    let maxPerSideDeltaObservedPt: Double
    let maxOriginPaddingObservedPt: Double
    let barredFromGeometry: Bool
}

struct OccludedCaptureRecord: Codable {
    let occluderCoverFrameTopLeft: [Double]
    let expectedBBoxPt: [Double]
    let imageWidthPx: Int
    let imageHeightPx: Int
    let scale: Double
    let markerFound: Bool
    let widthDeltaPt: Double
    let heightDeltaPt: Double
    let captureSurvivesFullOcclusion: Bool
    let occluderCoverHitsAtCapture: Int
    let atISO8601: String
}

struct CaptureMatrixRecord: Codable {
    let cells: [CaptureCell]
    let barredShadowBearingCells: [CaptureCell]
    let frozenRuleCount: Int
    let expectedBBoxUnionRule: String
    let shadowBearingBarredFromGeometry: Bool
    let occludedCapture: OccludedCaptureRecord?
    let noRuleFailClosedProved: Bool
    let noRuleFailClosedDetail: String
}

struct FrozenRuleValidation: Codable {
    let stateKey: String
    let barredFromGeometry: Bool
    let expectedVerdict: String
    let observedValidity: String
    let violations: [String]
    let asExpected: Bool
}

struct VisionLocalizationRecord: Codable {
    let titleFixture: String
    let otherTitleFixture: String
    let countFixture: String
    let menuRows: [String]
    let recognizedStrings: [String]
    let exactMenuRowMatch: Bool
    let exactMenuRowMatchCount: Int
    let exactCountMatch: Bool
    let exactTitleMatch: Bool
    let rowBoxesLocalPtAcrossCaptures: [[Double]]
    let rowBoxMaxCornerDeviationPt: Double
    let safePointsLocalPtAcrossCaptures: [[Double]]
    let safePointMaxDeviationPt: Double
    let safeInteriorDispatchable: Bool
    let discriminatorOtherTitleFound: Bool
    let discriminatorExpectedTitleAbsentWithOtherLabel: Bool
    let discriminatorExpectedTitleFoundAfterRestore: Bool
    let ambiguityMenuRows: [String]
    let ambiguityMatchCount: Int
    let ambiguityRefused: Bool
    let atISO8601: String
}

struct TransformRecord: Codable {
    let startFrameTopLeft: [Double]
    let positiveMoveFrameTopLeft: [Double]
    let negativeMoveFrameTopLeft: [Double]
    let scaleObserved: Double
    let backingScaleFactor: Double
    let localToScreenMaxErrorPt: Double
    let localToPixelToLocalMaxErrorPt: Double
    let pixelToScreenToPixelMaxErrorPt: Double
    let screenShiftAfterPositiveMoveErrorPt: Double
    let screenShiftAfterNegativeMoveErrorPt: Double
    let screenReturnToStartErrorPt: Double
    let wrongScaleDetected: Bool
    let wrongScaleDetail: String
    let safeInteriorRefusalDemonstrated: Bool
    let safeInteriorDetail: String
    let recordedBBoxDifferentialObserved: Bool
    let recordedBBoxObservationDetail: String
    let recordedBBoxMarkerErrorPt: Double
    let expectedBBoxMarkerErrorPt: Double
    let atISO8601: String
}

struct RoutingRecord: Codable {
    let popupFrameTopLeft: [Double]
    let popupRowPointScreen: [Double]
    let popupFrameRaisedAfterOccluderTopLeft: [Double]
    let popupRowPointAfterOccluderScreen: [Double]
    let popupHitsAfterPopupClick: Int
    let mainHitsAfterPopupClick: Int
    let lastPopupHitLocal: [Double]?
    let mainRowPointScreen: [Double]
    let mainHitsAfterMainClick: Int
    let popupHitsAfterMainClick: Int
    let lastMainHitLocal: [Double]?
    let occluderCoverFrameTopLeft: [Double]
    let occluderCoverHitsAfterCoveredMainClick: Int
    let mainHitsAfterCoveredMainClick: Int
    let lastCoverHitLocal: [Double]?
    let popupHitsAfterCoveredPopupClick: Int
    let mainHitsAfterCoveredPopupClick: Int
    let occluderCoverHitsAfterCoveredPopupClick: Int
    let harnessActiveAtCoveredPopupClick: Bool
    let occluderActiveAtCoveredPopupClick: Bool
    let occluderCoverVisibleAtCoveredPopupClick: Bool
    let popupTopmostOverOccluderProved: Bool
    let popupReceivesEventProved: Bool
    let mainWindowNotReceivingPopupEventProved: Bool
    let occluderOccludesMainWindowProved: Bool
    let atISO8601: String
}

struct ChooserAxCalibrationRecord: Codable {
    let harnessPID: Int32
    let harnessOwnedSCWindows: [[String: String]]
    let panelWindowFound: Bool
    let panelWindowRole: String?
    let panelWindowSubrole: String?
    let panelWindowTitle: String?
    let panelWindowFramePt: [Double]?
    let axNodeCount: Int
    let rolesObserved: [String]
    let subrolesObserved: [String]
    let buttonTitles: [String]
    let defaultButtonTitle: String?
    let defaultButtonKeyEquivalent: String?
    let textFieldRoles: [String]
    let popUpRoles: [String]
    let pathValueCandidates: [String]
    let axDumpNodeCount: Int
    let atISO8601: String
}

struct ChooserPredicateProofRecord: Codable {
    var predicateID: String
    var realPanelVerdict: String
    var realPanelDetail: String
    var fakeSameProcessVerdict: String
    var fakeSameProcessCause: String
    var fakeSameProcessDetail: String
    var emptyCensusFakeVerdict: String
    var emptyCensusFakeCause: String
    var occluderLookAlikeVerdict: String
    var occluderLookAlikeCause: String
    var ownershipUnboundVerdict: String
    var ownershipUnboundCause: String
    var pidReuseVerdict: String
    var pidReuseCause: String
    var notNewVerdict: String
    var notNewCause: String
    var navigationReflected: Bool
    var navigationCandidatesAfter: [String]
    var panelDirectoryAfterNavigation: String?
    var pressedButtonDescription: String?
    var confirmationAction: String
    var panelClosedResponse: Int?
    var confirmedDirectory: String?
    var markerPath: String?
    var markerVerified: Bool
    var inputPostsDuringFixture: Int
    var atISO8601: String
}

struct LatencySampleMs: Codable {
    let run: Int
    let delayMs: Int
    let willShowToShownMs: Double
    let shownEventAt: Double
}

struct PostconditionLatencyRecord: Codable {
    let runCount: Int
    let scheduledDelayMs: Int
    let samples: [LatencySampleMs]
    let maxMs: Double
    let medianMs: Double
    let p95Ms: Double
    let delayedPanelScheduledMs: Int
    let delayedPanelShownMs: Double
    let atISO8601: String
}

struct PostconditionBoundsFreeze: Codable {
    let frozenAtISO8601: String
    let runID: String
    let planTimeBounds: PostconditionBounds
    let frozenBounds: PostconditionBounds
    let measuredRuns: Int
    let maxObservedMs: Double
    let medianObservedMs: Double
    let p95ObservedMs: Double
    let rationale: String
    let latencyEvidenceName: String
    let latencyEvidenceSHA256: String
}

struct PostconditionProofRecord: Codable {
    var withinWindowOutcome: String
    var withinWindowDetail: String
    var timeoutOutcome: String
    var timeoutDetail: String
    var lateOutcome: String
    var lateDetail: String
    var lateAffirmationNonNil: Bool
    var lateDiagnosticAffirmed: Bool
    var lateDiagnosticDetail: String
    var zeroFurtherInputDuringMonitors: Bool
    var monitorInputPosts: Int
    var atISO8601: String
}

struct FocusTheftRecord: Codable {
    let focusLostDetected: Bool
    let focusLostDetail: String
    let recoveredAfterReactivation: Bool
    let frameChangeDetected: Bool
    let frameChangeDetail: String
    let identityRefreshAllowed: Bool
    let dispatchesPostedDuringFixture: Int
    let atISO8601: String
}

struct TripwireRecord: Codable {
    let fixtureRoot: String
    let stagingRunDir: String
    let approvedRoot: String
    let outsideDir: String
    let harnessPID: Int32
    let occluderPID: Int32
    let classifications: [TripwireClassification]
    let allExpectedOutcomesMatched: Bool
    let baselinePathEvent: TripwireClassification
    let baselineUntouchedNote: String
    let atISO8601: String
}

struct RestartPointRecord: Codable {
    let point: String
    let childPID: Int32
    let terminationStatus: Int32
    let terminationReason: String
    let sawSIGKILL: Bool
    let entriesAfterReload: Int
    let chainVerified: Bool
    let headMatchesChildHeadFile: Bool
    let headHash: String?
    let childHeadHash: String?
    let resumeMode: String
    let irreversibleDispatchCount: Int
    let allowedNewIrreversibleDispatches: Int
    let wouldRefuseNewIrreversibleDispatch: Bool
    let observedSeconds: Double
}

struct RestartFixtureRecord: Codable {
    let ledgerDir: String
    let points: [RestartPointRecord]
    let allPointsObserveOnly: Bool
    let allChainsContinuous: Bool
    let zeroNewIrreversibleDispatches: Bool
    let freshReviewedControl: String
    let atISO8601: String
}

private struct ChooserSamplerContext: Sendable {
    let harnessPID: Int32
    let mainWindowID: UInt32
    let popupWindowID: UInt32
    let predicate: ChooserAffirmationPredicate
    let preCensus: [Int32]
    let preWindowIDs: Set<UInt32>
}

/// Postcondition sampling runs outside the driver actor. Keeping this helper
/// independent of HarnessCalibrationDriver prevents each monitor sample from
/// hopping through MainActor while the bounded observation loop is suspended.
private enum ChooserAffirmationSampler {
    static func sample(context: ChooserSamplerContext) async -> PostconditionSample {
        do {
            let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
            let cgInventory = CGWindowInventory.onScreenWindows()
            let postCensus = Array(Set(content.windows.compactMap { $0.owningApplication?.processID })).sorted()
            let candidates = content.windows.filter { window in
                window.owningApplication?.processID == context.harnessPID
                    && window.isOnScreen
                    && window.windowID != context.mainWindowID
                    && window.windowID != context.popupWindowID
            }
            var rejectionDetails: [String] = []
            for window in candidates {
                guard let axElement = matchingAXWindow(pid: context.harnessPID, frame: window.frame) else { continue }
                let dump = AXDriver.dump(element: axElement, pid: context.harnessPID, maxDepth: 8, maxNodes: 500)
                let candidate = ChooserCandidate(
                    windowID: window.windowID,
                    frame: window.frame,
                    onScreen: true,
                    presentInSCInventory: true,
                    presentInCGInventory: cgInventory.contains { $0.windowNumber == window.windowID },
                    isNewRelativeToPreDispatchInventory: !context.preWindowIDs.contains(window.windowID),
                    owner: ProcessIdentity.reading(pid: context.harnessPID),
                    pidReuseDetected: false,
                    axNodes: dump.nodes,
                    preDispatchCensusPIDs: context.preCensus,
                    postDispatchCensusPIDs: postCensus
                )
                switch ChooserAffirmationEvaluator.evaluate(candidate: candidate, predicate: context.predicate) {
                case .affirmed:
                    return PostconditionSample(affirmed: ChooserAffirmation(
                        windowID: window.windowID,
                        frame: window.frame,
                        ownerPID: context.harnessPID,
                        predicateID: context.predicate.predicateID,
                        affirmedAtISO8601: EvidenceIO.iso8601()
                    ))
                case let .refused(cause, detail):
                    rejectionDetails.append("windowID=\(window.windowID) cause=\(cause.rawValue) \(detail)")
                }
            }
            let note = rejectionDetails.isEmpty
                ? "noEligibleChooserCandidate"
                : rejectionDetails.joined(separator: "; ")
            return PostconditionSample(affirmed: nil, note: note)
        } catch {
            return PostconditionSample(affirmed: nil, note: "samplerError:\(error)")
        }
    }

    private static func matchingAXWindow(pid: Int32, frame: CGRect) -> AXUIElement? {
        var best: (element: AXUIElement, distance: Double)?
        for window in AXDriver.windows(ofApp: pid) {
            guard let axFrame = AXDriver.frame(of: window) else { continue }
            let distance = Double(abs(axFrame.minX - frame.minX) + abs(axFrame.minY - frame.minY)
                + abs(axFrame.width - frame.width) + abs(axFrame.height - frame.height))
            if distance <= 6, best == nil || distance < best!.distance {
                best = (window, distance)
            }
        }
        return best?.element
    }
}

// MARK: - Driver

@MainActor
final class HarnessCalibrationDriver {
    private let options: CalibrationOptions
    private let run: EvidenceRun
    private var harness: ProcessPeer!
    private var occluder: ProcessPeer!
    private var itemResults: [ItemResult] = []
    private var frozenArtifacts: [FrozenArtifact] = []
    private var notes: [String] = []
    private let startedAt = Date()
    private let taskID = "T20260925-0647-01-rev28-native-closed-loop"
    private let sdkPath = ProcessInfo.processInfo.environment["REV28_SDK_PATH"] ?? "unknown"
    private let swiftVersion = ProcessInfo.processInfo.environment["REV28_SWIFT_VERSION"] ?? "unknown"
    private var frozenRuleBook: CaptureGeometryRuleBook?
    private var frozenPredicate: ChooserAffirmationPredicate?
    private var harnessState: [String: Any] = [:]
    private var inputPostCount = 0
    private var occluderCoveredFrameTopLeft: [Double]?

    init(options: CalibrationOptions, run: EvidenceRun) {
        self.options = options
        self.run = run
    }

    private func wants(_ item: Int) -> Bool { options.items.isEmpty || options.items.contains(item) }

    /// Dependent calibration items run in fresh evidence runs after item 1 has
    /// published its immutable canonical artifacts. Load that exact freeze only
    /// when item 1 is not part of this invocation, and fail closed unless a
    /// canonical checksum file binds both the rule book and its complete matrix.
    private func loadFrozenRuleBookIfNeeded() throws {
        guard !wants(1), [2, 3, 7].contains(where: { wants($0) }) else { return }

        let frozenDirectory = run.canonicalFrozenDir
        let ruleBookName = "capture-geometry-rulebook-v1.json"
        let matrixName = "capture-matrix-v1.json"
        let ruleBookURL = frozenDirectory.appendingPathComponent(ruleBookName)
        let matrixURL = frozenDirectory.appendingPathComponent(matrixName)
        let ruleBookData = try Data(contentsOf: ruleBookURL)
        let matrixData = try Data(contentsOf: matrixURL)
        let ruleBookSHA = EvidenceIO.sha256Hex(ruleBookData)
        let matrixSHA = EvidenceIO.sha256Hex(matrixData)

        let sumFiles = try FileManager.default.contentsOfDirectory(
            at: frozenDirectory,
            includingPropertiesForKeys: nil
        ).filter {
            $0.lastPathComponent.hasPrefix("sha256sums-HARNESS-")
                && $0.pathExtension == "txt"
        }.sorted { $0.lastPathComponent < $1.lastPathComponent }

        var sumRecords: [(url: URL, entries: [String: String])] = []
        for sumURL in sumFiles {
            let contents = try String(contentsOf: sumURL, encoding: .utf8)
            var entries: [String: String] = [:]
            for line in contents.split(whereSeparator: \.isNewline) {
                let columns = line.split(whereSeparator: { $0.isWhitespace })
                guard columns.count == 2 else { continue }
                let name = String(columns[1])
                guard entries[name] == nil else {
                    throw NSError(domain: "rev28ctl", code: 31, userInfo: [
                        NSLocalizedDescriptionKey: "duplicate entry for \(name) in \(sumURL.lastPathComponent)"
                    ])
                }
                entries[name] = String(columns[0])
            }
            sumRecords.append((sumURL, entries))
        }

        let pairedRecords = sumRecords.filter {
            $0.entries[ruleBookName] != nil && $0.entries[matrixName] != nil
        }
        let allRuleBookHashes = Set(sumRecords.compactMap { $0.entries[ruleBookName] })
        let allMatrixHashes = Set(sumRecords.compactMap { $0.entries[matrixName] })
        guard pairedRecords.count == 1,
              allRuleBookHashes == [ruleBookSHA],
              allMatrixHashes == [matrixSHA],
              pairedRecords[0].entries[ruleBookName] == ruleBookSHA,
              pairedRecords[0].entries[matrixName] == matrixSHA else {
            throw NSError(domain: "rev28ctl", code: 32, userInfo: [
                NSLocalizedDescriptionKey: "canonical capture artifacts lack one matching append-only SHA-256 pair"
            ])
        }

        let ruleBook = try JSONDecoder().decode(CaptureGeometryRuleBook.self, from: ruleBookData)
        let matrix = try JSONDecoder().decode(CaptureMatrixRecord.self, from: matrixData)
        var expectedRuleKeys = Set<String>()
        var expectedBarredKeys = Set<String>()
        for settled in [false, true] {
            for activated in [false, true] {
                for includeChildWindows in [false, true] {
                    expectedRuleKeys.insert(CaptureGeometryRules.stateKey(CaptureGeometryState(
                        settled: settled,
                        activated: activated,
                        includeChildWindows: includeChildWindows,
                        ignoreShadows: true
                    )))
                    expectedBarredKeys.insert(CaptureGeometryRules.stateKey(CaptureGeometryState(
                        settled: settled,
                        activated: activated,
                        includeChildWindows: includeChildWindows,
                        ignoreShadows: false
                    )))
                }
            }
        }

        let completeShadowFreeMatrix = matrix.cells.count == 8
            && Set(matrix.cells.map(\.stateKey)) == expectedRuleKeys
            && matrix.cells.allSatisfy {
                !$0.shadowsOn && $0.ignoreShadows && !$0.barredFromGeometry
                    && $0.requestedActivated == $0.observedActivated
                    && !$0.samples.isEmpty
                    && $0.samples.allSatisfy { $0.scale == $0.backingScaleFactor }
            }
        let completeShadowBearingMatrix = matrix.barredShadowBearingCells.count == 8
            && Set(matrix.barredShadowBearingCells.map(\.stateKey)) == expectedBarredKeys
            && matrix.barredShadowBearingCells.allSatisfy {
                $0.shadowsOn && !$0.ignoreShadows && $0.barredFromGeometry
                    && $0.requestedActivated == $0.observedActivated
                    && !$0.samples.isEmpty
                    && $0.samples.allSatisfy { $0.scale == $0.backingScaleFactor }
            }
        let validRules = ruleBook.rules.values.allSatisfy {
            $0.maxPerSideSizeDeltaPt.isFinite
                && $0.maxPerSideSizeDeltaPt >= 0
                && $0.originPaddingPt.isFinite
                && $0.originPaddingPt >= 0
                && $0.maxOriginPaddingPt.isFinite
                && $0.maxOriginPaddingPt >= $0.originPaddingPt
        }
        guard ruleBook.ruleID == "rev28-capture-geometry-v1",
              Set(ruleBook.rules.keys) == expectedRuleKeys,
              validRules,
              matrix.frozenRuleCount == 8,
              matrix.shadowBearingBarredFromGeometry,
              matrix.noRuleFailClosedProved,
              completeShadowFreeMatrix,
              completeShadowBearingMatrix,
              matrix.occludedCapture?.captureSurvivesFullOcclusion == true else {
            throw NSError(domain: "rev28ctl", code: 33, userInfo: [
                NSLocalizedDescriptionKey: "canonical capture artifacts do not prove the complete validated 16-cell matrix"
            ])
        }

        frozenRuleBook = ruleBook
        run.recordSHA(name: "loaded-canonical/\(ruleBookName)", sha: ruleBookSHA)
        run.recordSHA(name: "loaded-canonical/\(matrixName)", sha: matrixSHA)
        notes.append(
            "Loaded canonical capture freeze: rulebook SHA-256 \(ruleBookSHA), matrix SHA-256 \(matrixSHA), checksum file \(pairedRecords[0].url.lastPathComponent)"
        )
    }

    /// The postcondition monitor can run independently once item 6 has
    /// published its immutable predicate freeze. Validate that exact canonical
    /// artifact and checksum before using it in a fresh driver process.
    private func loadFrozenPredicateIfNeeded() throws {
        guard wants(5), !wants(6) else { return }

        let frozenDirectory = run.canonicalFrozenDir
        let predicateName = "chooser-affirmation-predicate-v2.json"
        let predicateURL = frozenDirectory.appendingPathComponent(predicateName)
        let predicateData = try Data(contentsOf: predicateURL)
        let predicateSHA = EvidenceIO.sha256Hex(predicateData)
        let sumFiles = try FileManager.default.contentsOfDirectory(
            at: frozenDirectory,
            includingPropertiesForKeys: nil
        ).filter {
            $0.lastPathComponent.hasPrefix("sha256sums-HARNESS-")
                && $0.pathExtension == "txt"
        }.sorted { $0.lastPathComponent < $1.lastPathComponent }

        var referencedSHAs: [String] = []
        var matchingFiles: [URL] = []
        for sumURL in sumFiles {
            let contents = try String(contentsOf: sumURL, encoding: .utf8)
            var entries: [String: String] = [:]
            for line in contents.split(whereSeparator: \.isNewline) {
                let columns = line.split(whereSeparator: { $0.isWhitespace })
                guard columns.count == 2 else { continue }
                let name = String(columns[1])
                guard entries[name] == nil else {
                    throw NSError(domain: "rev28ctl", code: 34, userInfo: [
                        NSLocalizedDescriptionKey: "duplicate entry for \(name) in \(sumURL.lastPathComponent)"
                    ])
                }
                entries[name] = String(columns[0])
            }
            if let sha = entries[predicateName] {
                referencedSHAs.append(sha)
                matchingFiles.append(sumURL)
            }
        }
        guard matchingFiles.count == 1, Set(referencedSHAs) == [predicateSHA] else {
            throw NSError(domain: "rev28ctl", code: 35, userInfo: [
                NSLocalizedDescriptionKey: "canonical chooser predicate lacks one matching append-only SHA-256 record"
            ])
        }

        let predicate = try JSONDecoder().decode(ChooserAffirmationPredicate.self, from: predicateData)
        guard predicate.predicateID == "rev28-chooser-affirmation-v1",
              predicate.ax.windowRole == "AXWindow",
              predicate.ax.allowedSubroles.contains("AXStandardWindow"),
              predicate.ax.requiresTextField,
              predicate.ax.requiresPopUpButton,
              predicate.ax.requiresPathAffordance,
              predicate.ownership.requiresOwningPIDInCensusUnion,
              predicate.ownership.requiresStableProcessInstance,
              predicate.ownership.emptyPreCensusWidensRefusal else {
            throw NSError(domain: "rev28ctl", code: 36, userInfo: [
                NSLocalizedDescriptionKey: "canonical chooser predicate does not preserve the validated S-06 clauses"
            ])
        }

        frozenPredicate = predicate
        run.recordSHA(name: "loaded-canonical/\(predicateName)", sha: predicateSHA)
        notes.append(
            "Loaded canonical chooser predicate SHA-256 \(predicateSHA), checksum file \(matchingFiles[0].lastPathComponent)"
        )
    }

    func runAll() async -> Int32 {
        do {
            try loadFrozenRuleBookIfNeeded()
            try loadFrozenPredicateIfNeeded()
            _ = NSApplication.shared
            try startPeers()
            if wants(1) { try await item01CaptureMatrix() }
            if wants(2) { try await item02VisionLocalization() }
            if wants(3) { try await item03Transforms() }
            if wants(4) { try await item04QuartzRouting() }
            if wants(6) { try await item06ChooserPredicate() }
            if wants(5) { try await item05Postcondition() }
            if wants(7) { try await item07FocusTheft() }
            if wants(8) { try await item08TripwireAttribution() }
            if wants(9) { try await item09RestartFixture() }
        } catch {
            notes.append("driverError: \(error)")
            await writeSummary(verdict: "FAIL")
            stopPeers()
            return 2
        }
        stopPeers()
        let verdict = itemResults.allSatisfy { $0.verdict == "PASS" } ? "PASS" : "PARTIAL"
        await writeSummary(verdict: verdict)
        return verdict == "PASS" ? 0 : 1
    }

    private func startPeers() throws {
        try EvidenceIO.ensureDirectory(run.logsDir)
        let harnessURL = options.binaryDirectory.appendingPathComponent("rev28harness")
        let occluderURL = options.binaryDirectory.appendingPathComponent("rev28occluder")
        harness = try ProcessPeer(
            executableURL: harnessURL,
            arguments: [],
            name: "rev28harness",
            logURL: run.logsDir.appendingPathComponent("rev28harness-stdout.log")
        )
        occluder = try ProcessPeer(
            executableURL: occluderURL,
            arguments: [],
            name: "rev28occluder",
            logURL: run.logsDir.appendingPathComponent("rev28occluder-stdout.log")
        )
    }

    private func stopPeers() {
        harness?.terminate()
        occluder?.terminate()
    }

    private func writeSummary(verdict: String) async {
        let summary = CalibrationSummary(
            taskID: taskID,
            runID: run.runID,
            startedAtISO8601: EvidenceIO.iso8601(startedAt),
            finishedAtISO8601: EvidenceIO.iso8601(),
            driverExecutable: Bundle.main.executableURL?.path ?? CommandLine.arguments[0],
            driverPID: getpid(),
            harnessExecutable: options.binaryDirectory.appendingPathComponent("rev28harness").path,
            harnessPID: harness?.process.processIdentifier ?? -1,
            occluderPID: occluder?.process.processIdentifier ?? -1,
            sdkPath: sdkPath,
            swiftVersion: swiftVersion,
            hostOSVersion: ProcessInfo.processInfo.operatingSystemVersionString,
            axTrusted: AXDriver.isProcessTrusted(),
            screenCaptureTrusted: CGPreflightScreenCaptureAccess(),
            postEventTrusted: CGPreflightPostEventAccess(),
            screenHeightPt: Double(NSScreen.screens.first?.frame.height ?? 0),
            backingScaleFactor: Double(NSScreen.screens.first?.backingScaleFactor ?? 0),
            items: itemResults,
            frozen: frozenArtifacts,
            verdict: verdict,
            notes: notes
        )
        do {
            let result = try run.writeItemRecord("00-calibration-summary.json", summary)
            _ = try run.writeSHA256Sums()
            if !frozenArtifacts.isEmpty {
                let canonicalSums = try run.writeCanonicalSHA256Sums()
                FileHandle.standardOutput.write(Data("canonical sha256sums: \(canonicalSums)\n".utf8))
            }
            FileHandle.standardOutput.write(Data("summary: \(result.path) sha256=\(result.sha)\n".utf8))
        } catch {
            FileHandle.standardOutput.write(Data("summary write failed: \(error)\n".utf8))
        }
    }

    private func recordItem(_ item: Int, name: String, verdict: String, detail: String, fileName: String, value: some Encodable) async throws {
        let written = try run.writeItemRecord(fileName, value)
        itemResults.append(ItemResult(
            item: item,
            name: name,
            verdict: verdict,
            detail: detail,
            evidencePath: written.path,
            evidenceSHA256: written.sha
        ))
        FileHandle.standardOutput.write(Data("item \(item) \(name): \(verdict) - \(detail)\n".utf8))
    }

    private func recordFrozen(_ name: String, value: some Encodable) throws {
        let written = try run.writeFrozen(name, value)
        frozenArtifacts.append(FrozenArtifact(name: name, path: written.path, sha256: written.sha))
        FileHandle.standardOutput.write(Data("frozen \(name): sha256=\(written.sha)\n".utf8))
    }

    // MARK: - Peer/OS helpers

    private func harnessCall(_ command: String, params: [String: Any] = [:], timeout: Double = 20) async throws -> [String: Any] {
        let reply = try await harness.send(command, params: params, timeoutSeconds: timeout)
        if (reply["ok"] as? Bool) != true {
            throw NSError(domain: "rev28ctl", code: 4, userInfo: [NSLocalizedDescriptionKey: "harness \(command) failed: \(reply["error"] ?? "unknown")"])
        }
        return reply
    }

    private func occluderCall(_ command: String, params: [String: Any] = [:], timeout: Double = 20) async throws -> [String: Any] {
        let reply = try await occluder.send(command, params: params, timeoutSeconds: timeout)
        if (reply["ok"] as? Bool) != true {
            throw NSError(domain: "rev28ctl", code: 5, userInfo: [NSLocalizedDescriptionKey: "occluder \(command) failed: \(reply["error"] ?? "unknown")"])
        }
        return reply
    }

    private func refreshHarnessState() async throws {
        harnessState = try await harnessCall("state")
    }

    private func harnessPID() -> Int32 { harness.process.processIdentifier }

    private func harnessActive() -> Bool { (harnessState["active"] as? NSNumber)?.boolValue ?? false }

    private func popupWindowNumber() -> UInt32 { UInt32((harnessState["popupWindowNumber"] as? NSNumber)?.uint32Value ?? 0) }

    private func mainWindowNumber() -> UInt32 { UInt32((harnessState["mainWindowNumber"] as? NSNumber)?.uint32Value ?? 0) }

    private func contentOriginLocalTopLeft() -> CGPoint {
        guard let dict = harnessState["contentOriginLocalTopLeft"] as? [String: Any],
              let x = (dict["x"] as? NSNumber)?.doubleValue,
              let y = (dict["y"] as? NSNumber)?.doubleValue else { return .zero }
        return CGPoint(x: x, y: y)
    }

    private func arrayFromRect(_ rect: CGRect) -> [Double] {
        [Double(rect.origin.x), Double(rect.origin.y), Double(rect.width), Double(rect.height)]
    }

    private func pointArray(_ point: CGPoint) -> [Double] { [Double(point.x), Double(point.y)] }

    private func dictRect(_ value: Any?) -> CGRect? {
        guard let dict = value as? [String: Any],
              let x = (dict["x"] as? NSNumber)?.doubleValue,
              let y = (dict["y"] as? NSNumber)?.doubleValue,
              let w = (dict["w"] as? NSNumber)?.doubleValue,
              let h = (dict["h"] as? NSNumber)?.doubleValue else {
            return nil
        }
        return CGRect(x: x, y: y, width: w, height: h)
    }

    private func dictPoint(_ value: Any?) -> CGPoint? {
        guard let dict = value as? [String: Any],
              let x = (dict["x"] as? NSNumber)?.doubleValue,
              let y = (dict["y"] as? NSNumber)?.doubleValue else {
            return nil
        }
        return CGPoint(x: x, y: y)
    }

    private func freshContent() async throws -> SCShareableContent {
        try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
    }

    private func harnessMainWindow(in content: SCShareableContent) -> SCWindow? {
        let pid = harnessPID()
        let owned = content.windows.filter { $0.owningApplication?.processID == pid && $0.isOnScreen }
        if let mainNumber = content.windows.first(where: { $0.windowID == mainWindowNumber() && $0.owningApplication?.processID == pid }) {
            return mainNumber
        }
        if let titled = owned.first(where: { $0.title == "rev28 harness main" }) {
            return titled
        }
        return owned
            .filter { $0.windowLayer == 0 }
            .max { lhs, rhs in lhs.frame.width * lhs.frame.height < rhs.frame.width * rhs.frame.height }
    }

    private func popupWindow(in content: SCShareableContent) -> SCWindow? {
        let pid = harnessPID()
        let number = popupWindowNumber()
        return content.windows.first { $0.owningApplication?.processID == pid && $0.windowID == number && $0.isOnScreen }
    }

    private func harnessSnapshots(in content: SCShareableContent) -> [SCWindowSnapshot] {
        WindowSensor.snapshots(from: content).filter { $0.ownerPID == harnessPID() }
    }

    private func waitForSettle(_ seconds: Double = 1.0) async {
        try? await Task.sleep(nanoseconds: UInt64(seconds * 1_000_000_000))
    }

    private func sleep(milliseconds: Int) async {
        try? await Task.sleep(nanoseconds: UInt64(milliseconds) * 1_000_000)
    }

    private func occluderCoverTopLeft(nearMain: CGRect, screenHeight: Double, screenWidth: Double) -> CGRect {
        let coverWidth: Double = 300
        let coverHeight: Double = 260
        let x = min(max(nearMain.maxX + 40, 0), max(0, screenWidth - coverWidth - 10))
        let y = min(max(120, 0), max(0, screenHeight - coverHeight - 10))
        return CGRect(x: x, y: y, width: coverWidth, height: coverHeight)
    }

    private func configuration(includeChild: Bool, ignoreShadows: Bool) -> CaptureConfiguration {
        CaptureConfiguration(
            kind: includeChild ? .windowUnionWithChildWindows : .window,
            includeChildWindows: includeChild,
            ignoreShadows: ignoreShadows,
            ignoreClipping: false,
            showsCursor: false
        )
    }

    // MARK: - Item 1: capture per-state matrix + rule freeze

    private func item01CaptureMatrix() async throws {
        try await refreshHarnessState()
        _ = try await harnessCall("setShadows", params: ["on": true])
        _ = try await harnessCall("activate")
        _ = try await harnessCall("setFrame", params: ["x": 160.0, "y": 140.0, "w": 800.0, "h": 600.0])
        await waitForSettle(1.2)

        var cells: [CaptureCell] = []
        var barredCells: [CaptureCell] = []
        var noRuleFailClosedProved = false
        var noRuleFailClosedDetail = "not exercised"

        var combos: [(settled: Bool, activated: Bool, shadowsOn: Bool, includeChild: Bool)] = {
            var result: [(Bool, Bool, Bool, Bool)] = []
            for settled in [true, false] {
                for activated in [true, false] {
                    for shadowsOn in [true, false] {
                        for includeChild in [true, false] {
                            result.append((settled, activated, shadowsOn, includeChild))
                        }
                    }
                }
            }
            return result
        }()
        var partialMatrix = false
        if let maxCells = options.maxCells, maxCells < combos.count {
            combos = Array(combos.prefix(maxCells))
            partialMatrix = true
            notes.append("PARTIAL: capture matrix limited to the first \(maxCells) of 16 cells by --max-cells; the frozen rule book is PARTIAL / NOT_FROZEN for the remaining states")
        }

        let screen = NSScreen.screens.first
        let screenHeight = Double(screen?.frame.height ?? 0)
        let screenWidth = Double(screen?.frame.width ?? 0)

        for combo in combos {
            if combo.includeChild {
                _ = try await harnessCall("showPopup", params: ["dx": 700.0, "dy": 560.0])
            } else {
                _ = try await harnessCall("hidePopup")
            }
            _ = try await harnessCall("setShadows", params: ["on": combo.shadowsOn])
            if combo.activated {
                _ = try await harnessCall("activate")
                if let cover = occluderCoveredFrameTopLeft {
                    _ = cover
                    _ = try await occluderCall("hide")
                    occluderCoveredFrameTopLeft = nil
                }
            } else {
                try await refreshHarnessState()
                if let mainFrame = dictRect(harnessState["mainFrameTopLeft"]) {
                    let coverRect = occluderCoverTopLeft(nearMain: mainFrame, screenHeight: screenHeight, screenWidth: screenWidth)
                    _ = try await occluderCall("cover", params: ["x": Double(coverRect.origin.x), "y": Double(coverRect.origin.y), "w": Double(coverRect.width), "h": Double(coverRect.height), "activate": true])
                    occluderCoveredFrameTopLeft = [Double(coverRect.origin.x), Double(coverRect.origin.y)]
                }
            }
            await waitForSettle(0.45)

            var samples: [CaptureCellSample] = []
            var cellState: CaptureGeometryState?
            for attempt in 1...2 {
                if combo.settled {
                    _ = try await harnessCall("moveBy", params: ["dx": 5.0, "dy": 3.0])
                    await waitForSettle(1.0)
                } else {
                    _ = try await harnessCall("moveBy", params: ["dx": 6.0, "dy": 4.0])
                    await sleep(milliseconds: 25)
                }
                try await refreshHarnessState()
                let content = try await freshContent()
                guard let main = harnessMainWindow(in: content) else {
                    throw NSError(domain: "rev28ctl", code: 6, userInfo: [NSLocalizedDescriptionKey: "harness main window not found"])
                }
                let popup = combo.includeChild ? popupWindow(in: content) : nil
                let snapshots = harnessSnapshots(in: content)
                let includedIDs = Set([main.windowID] + (popup.map { [$0.windowID] } ?? []))
                let included = snapshots.filter { includedIDs.contains($0.windowID) }
                let expected = FrameCaptureSupport.unionBBox(of: included, fallback: main.frame)
                let observedActivated = harnessActive()
                let state = CaptureGeometryState(
                    settled: combo.settled,
                    activated: observedActivated,
                    includeChildWindows: combo.includeChild,
                    ignoreShadows: !combo.shadowsOn
                )
                cellState = cellState ?? state
                let cfg = configuration(includeChild: combo.includeChild, ignoreShadows: !combo.shadowsOn)

                var noRuleValidity: String?
                var noRuleViolations: [String] = []
                if attempt == 1 {
                    let probeService = FrameCaptureService(ruleBook: nil)
                    let probe = try await probeService.capture(
                        window: main,
                        configuration: cfg,
                        includedWindows: included,
                        state: state,
                        identityTemplate: nil
                    )
                    noRuleValidity = probe.validity.rawValue
                    noRuleViolations = probe.violations
                    let failClosed = probe.validity == .invalid && probe.violations.contains { $0.contains("noFrozenRule") }
                    if failClosed {
                        noRuleFailClosedProved = true
                        noRuleFailClosedDetail = "stateKey=\(CaptureGeometryRules.stateKey(state)) validity=\(probe.validity.rawValue) violations=\(probe.violations)"
                    }
                }

                let image = try await RawCapture.capture(window: main, configuration: cfg)
                let scale = Double(SCContentFilter(desktopIndependentWindow: main).pointPixelScale)
                let backing = FrameCaptureSupport.backingScaleFactor(forWindowFrame: main.frame) ?? -1
                let widthPt = Double(image.width) / scale
                let heightPt = Double(image.height) / scale
                let deltaW = widthPt - Double(expected.width)
                let deltaH = heightPt - Double(expected.height)
                let perSide = SideDelta(top: deltaH / 2.0, left: deltaW / 2.0, bottom: deltaH / 2.0, right: deltaW / 2.0)

                let origin = contentOriginLocalTopLeft()
                var probeRecord: OriginProbe?
                var offsetX: Double?
                var offsetY: Double?
                if let marker = PixelProbe.findRedSquareTopLeft(in: image) {
                    let expectedMarkerX = Double(main.frame.minX) + Double(origin.x) + 4.0
                    let expectedMarkerY = Double(main.frame.minY) + Double(origin.y) + 4.0
                    let foundX = Double(marker.x) / scale
                    let foundY = Double(marker.y) / scale
                    offsetX = foundX - (expectedMarkerX - Double(expected.minX))
                    offsetY = foundY - (expectedMarkerY - Double(expected.minY))
                    probeRecord = OriginProbe(
                        markerFound: true,
                        expectedMarkerScreenPt: [expectedMarkerX, expectedMarkerY],
                        foundMarkerPixel: [Double(marker.x), Double(marker.y)],
                        measuredOriginOffsetXPt: offsetX,
                        measuredOriginOffsetYPt: offsetY
                    )
                } else {
                    probeRecord = OriginProbe(
                        markerFound: false,
                        expectedMarkerScreenPt: [],
                        foundMarkerPixel: nil,
                        measuredOriginOffsetXPt: nil,
                        measuredOriginOffsetYPt: nil
                    )
                }

                samples.append(CaptureCellSample(
                    settled: combo.settled,
                    requestedActivated: combo.activated,
                    observedActivated: observedActivated,
                    shadowsOn: combo.shadowsOn,
                    ignoreShadows: !combo.shadowsOn,
                    includeChildWindows: combo.includeChild,
                    stateKey: CaptureGeometryRules.stateKey(state),
                    attempt: attempt,
                    expectedBBoxPt: arrayFromRect(expected),
                    imageWidthPx: image.width,
                    imageHeightPx: image.height,
                    scale: scale,
                    backingScaleFactor: backing,
                    perSideDeltaPt: [
                        "top": perSide.top,
                        "left": perSide.left,
                        "bottom": perSide.bottom,
                        "right": perSide.right,
                    ],
                    measuredMaxPerSideDeltaPt: perSide.maximum,
                    noRuleValidity: noRuleValidity,
                    noRuleViolations: noRuleViolations,
                    originProbe: probeRecord,
                    capturedAtISO8601: EvidenceIO.iso8601()
                ))
            }

            guard let firstState = cellState else { continue }
            let maxPerSide = samples.map { $0.measuredMaxPerSideDeltaPt }.max() ?? 0
            let maxOrigin = samples.reduce(0.0) { partial, sample in
                let probeOffsets = [sample.originProbe?.measuredOriginOffsetXPt ?? 0, sample.originProbe?.measuredOriginOffsetYPt ?? 0]
                let fromSize = [sample.perSideDeltaPt["left"] ?? 0, sample.perSideDeltaPt["top"] ?? 0]
                return max(partial, (probeOffsets + fromSize).max() ?? 0)
            }
            let cell = CaptureCell(
                settled: combo.settled,
                requestedActivated: combo.activated,
                observedActivated: samples.first?.observedActivated ?? false,
                shadowsOn: combo.shadowsOn,
                ignoreShadows: !combo.shadowsOn,
                includeChildWindows: combo.includeChild,
                stateKey: CaptureGeometryRules.stateKey(firstState),
                samples: samples,
                maxPerSideDeltaObservedPt: maxPerSide,
                maxOriginPaddingObservedPt: maxOrigin,
                barredFromGeometry: combo.shadowsOn
            )
            if combo.shadowsOn { barredCells.append(cell) } else { cells.append(cell) }
        }

        // Freeze the rule book from the shadow-free cells only (plan invariant 1:
        // shadow-bearing captures are barred from geometry).
        var rules: [String: CaptureGeometryRule] = [:]
        for cell in cells {
            let padding: Double
            if cell.maxOriginPaddingObservedPt <= 0.5 {
                padding = 0
            } else {
                padding = (cell.maxOriginPaddingObservedPt * 4).rounded(.up) / 4
            }
            let maxPerSide = (cell.maxPerSideDeltaObservedPt).rounded(.up) + 1.0
            rules[cell.stateKey] = CaptureGeometryRule(
                maxPerSideSizeDeltaPt: maxPerSide,
                originPaddingPt: padding,
                maxOriginPaddingPt: padding + 1.0,
                notes: "W2 calibration run \(run.runID); samples=\(cell.samples.count); observed maxPerSide=\(cell.maxPerSideDeltaObservedPt) pt; observed originPadding=\(cell.maxOriginPaddingObservedPt) pt"
            )
        }
        let ruleBook = CaptureGeometryRuleBook(
            ruleID: "rev28-capture-geometry-v1",
            frozenAtISO8601: EvidenceIO.iso8601(),
            rules: rules
        )
        frozenRuleBook = ruleBook

        // Validate the frozen book per cell: shadow-free must be valid;
        // shadow-bearing must stay INVALID (no frozen rule -> fail-closed).
        var validations: [FrozenRuleValidation] = []
        for cell in (cells + barredCells) {
            if cell.includeChildWindows {
                _ = try await harnessCall("showPopup", params: ["dx": 700.0, "dy": 560.0])
            } else {
                _ = try await harnessCall("hidePopup")
            }
            _ = try await harnessCall("setShadows", params: ["on": cell.shadowsOn])
            if cell.requestedActivated {
                _ = try await harnessCall("activate")
            } else {
                try await refreshHarnessState()
                if let mainFrame = dictRect(harnessState["mainFrameTopLeft"]) {
                    let coverRect = occluderCoverTopLeft(nearMain: mainFrame, screenHeight: screenHeight, screenWidth: screenWidth)
                    _ = try await occluderCall("cover", params: ["x": Double(coverRect.origin.x), "y": Double(coverRect.origin.y), "w": Double(coverRect.width), "h": Double(coverRect.height), "activate": true])
                }
            }
            await waitForSettle(0.6)
            try await refreshHarnessState()
            let content = try await freshContent()
            guard let main = harnessMainWindow(in: content) else { continue }
            let popup = cell.includeChildWindows ? popupWindow(in: content) : nil
            let snapshots = harnessSnapshots(in: content)
            let includedIDs = Set([main.windowID] + (popup.map { [$0.windowID] } ?? []))
            let included = snapshots.filter { includedIDs.contains($0.windowID) }
            let state = CaptureGeometryState(
                settled: cell.settled,
                activated: harnessActive(),
                includeChildWindows: cell.includeChildWindows,
                ignoreShadows: cell.ignoreShadows
            )
            let cfg = configuration(includeChild: cell.includeChildWindows, ignoreShadows: cell.ignoreShadows)
            let service = FrameCaptureService(ruleBook: ruleBook)
            let record = try await service.capture(
                window: main,
                configuration: cfg,
                includedWindows: included,
                state: state,
                identityTemplate: nil
            )
            let expectedVerdict = cell.barredFromGeometry ? "invalid" : "valid"
            let asExpected = cell.barredFromGeometry
                ? (record.validity == .invalid && record.violations.contains { $0.contains("noFrozenRule") })
                : (record.validity == .valid)
            validations.append(FrozenRuleValidation(
                stateKey: CaptureGeometryRules.stateKey(state),
                barredFromGeometry: cell.barredFromGeometry,
                expectedVerdict: expectedVerdict,
                observedValidity: record.validity.rawValue,
                violations: record.violations,
                asExpected: asExpected
            ))
        }

        // Capture must survive full occlusion by the separate-process occluder.
        var occludedRecord: OccludedCaptureRecord?
        _ = try await harnessCall("hidePopup")
        _ = try await harnessCall("setShadows", params: ["on": true])
        _ = try await harnessCall("activate")
        await waitForSettle(0.8)
        try await refreshHarnessState()
        if let mainFrame = dictRect(harnessState["mainFrameTopLeft"]) {
            let cover = try await occluderCall("cover", params: ["x": Double(mainFrame.origin.x), "y": Double(mainFrame.origin.y), "w": Double(mainFrame.width), "h": Double(mainFrame.height), "activate": true])
            await waitForSettle(0.7)
            let content = try await freshContent()
            if let main = harnessMainWindow(in: content) {
                let snapshots = harnessSnapshots(in: content).filter { $0.windowID == main.windowID }
                let expected = FrameCaptureSupport.unionBBox(of: snapshots, fallback: main.frame)
                let cfg = configuration(includeChild: false, ignoreShadows: true)
                let image = try await RawCapture.capture(window: main, configuration: cfg)
                let scale = Double(SCContentFilter(desktopIndependentWindow: main).pointPixelScale)
                let widthDelta = Double(image.width) / scale - Double(expected.width)
                let heightDelta = Double(image.height) / scale - Double(expected.height)
                let marker = PixelProbe.findRedSquareTopLeft(in: image)
                let coverFrame = dictRect(cover["frameTopLeft"]) ?? mainFrame
                occludedRecord = OccludedCaptureRecord(
                    occluderCoverFrameTopLeft: arrayFromRect(coverFrame),
                    expectedBBoxPt: arrayFromRect(expected),
                    imageWidthPx: image.width,
                    imageHeightPx: image.height,
                    scale: scale,
                    markerFound: marker != nil,
                    widthDeltaPt: widthDelta,
                    heightDeltaPt: heightDelta,
                    captureSurvivesFullOcclusion: marker != nil && abs(widthDelta) <= 2.0 && abs(heightDelta) <= 2.0,
                    occluderCoverHitsAtCapture: 0,
                    atISO8601: EvidenceIO.iso8601()
                )
            }
        }
        _ = try await occluderCall("hide")
        _ = try await harnessCall("activate")

        let matrix = CaptureMatrixRecord(
            cells: cells,
            barredShadowBearingCells: barredCells,
            frozenRuleCount: rules.count,
            expectedBBoxUnionRule: "expectedBBox = union of freshly read SCWindow.frame of included windows (main [+ popup child window when includeChildWindows=true])",
            shadowBearingBarredFromGeometry: true,
            occludedCapture: occludedRecord,
            noRuleFailClosedProved: noRuleFailClosedProved,
            noRuleFailClosedDetail: noRuleFailClosedDetail
        )
        let allValid = validations.allSatisfy { $0.asExpected }
        let complete = !partialMatrix && cells.count == 8 && barredCells.count == 8
        let verdict = (allValid && noRuleFailClosedProved && (occludedRecord?.captureSurvivesFullOcclusion ?? false) && complete) ? "PASS" : "PARTIAL"
        let detail = "cells=\(cells.count)/8 shadowFree, barred=\(barredCells.count)/8 shadowBearing, frozenRules=\(rules.count) \(complete ? "(complete matrix)" : "(PARTIAL: --max-cells)") validationsAsExpected=\(validations.filter { $0.asExpected }.count)/\(validations.count) noRuleFailClosed=\(noRuleFailClosedProved) occlusionCapture=\(occludedRecord?.captureSurvivesFullOcclusion ?? false)"
        try await recordItem(1, name: "capture-matrix+rule-freeze", verdict: verdict, detail: detail, fileName: "01-capture-matrix.json", value: matrix)
        try await recordItem(1, name: "frozen-rule-validation", verdict: allValid ? "PASS" : "PARTIAL", detail: "per-state validation of frozen rule book", fileName: "01-frozen-rule-validation.json", value: validations)
        // Only a complete 16-cell matrix may publish canonical frozen artifacts:
        // a --max-cells partial run is evidence, never a freeze.
        if complete {
            try recordFrozen("capture-geometry-rulebook-v1.json", value: ruleBook)
            try recordFrozen("capture-matrix-v1.json", value: matrix)
        } else {
            notes.append("NOT_FROZEN: capture-geometry-rulebook-v1.json and capture-matrix-v1.json were NOT written to the canonical frozen/ dir (partial matrix: \(partialMatrix ? "--max-cells partial run" : "cells incomplete")); rerun the full 16-cell matrix to freeze")
        }
    }

    // MARK: - Item 2: Vision localization

    private func item02VisionLocalization() async throws {
        _ = try await harnessCall("hidePopup")
        _ = try await harnessCall("setShadows", params: ["on": true])
        _ = try await harnessCall("activate")
        _ = try await harnessCall("setFrame", params: ["x": 160.0, "y": 140.0, "w": 800.0, "h": 600.0])
        _ = try await harnessCall("setTitle", params: ["title": "旻謙允禎成長日記"])
        _ = try await harnessCall("setCountText", params: ["text": "57張照片"])
        let defaultRows = ["選擇項目", "修改相簿名稱", "儲存全部", "刪除相簿", "分享相簿"]
        _ = try await harnessCall("setMenuRows", params: ["rows": defaultRows])
        await waitForSettle(1.2)

        let ocr = VisionOcrEngine()
        var recognized: [String] = []
        var rowBoxes: [[Double]] = []
        var safePoints: [[Double]] = []
        var rowMatchCount = 0
        var countMatch = false
        var titleMatch = false

        for _ in 1...3 {
            try await refreshHarnessState()
            let content = try await freshContent()
            guard let main = harnessMainWindow(in: content) else { continue }
            let snapshots = harnessSnapshots(in: content).filter { $0.windowID == main.windowID }
            let state = CaptureGeometryState(settled: true, activated: harnessActive(), includeChildWindows: false, ignoreShadows: true)
            let cfg = configuration(includeChild: false, ignoreShadows: true)
            let service = FrameCaptureService(ruleBook: frozenRuleBook)
            let record = try await service.capture(window: main, configuration: cfg, includedWindows: snapshots, state: state, identityTemplate: nil)
            let image = try await RawCapture.capture(window: main, configuration: cfg)
            let items = try await ocr.recognize(image: image)
            recognized.append(contentsOf: items.map { $0.text })
            let menuMatches = OcrTextIdentity.exactMatches(in: items, expected: "儲存全部")
            rowMatchCount = menuMatches.count
            countMatch = !OcrTextIdentity.exactMatches(in: items, expected: "57張照片").isEmpty
            titleMatch = !OcrTextIdentity.exactMatches(in: items, expected: "旻謙允禎成長日記").isEmpty
            guard record.validity == .valid else { continue }
            let geometry = CaptureGeometry(windowFrame: main.frame, captureBBox: record.actualBBoxPt, scale: record.scale)
            if let match = menuMatches.first {
                let boxPx = match.boundingBoxCapturePx
                let topLeftPx = CGPoint(x: boxPx.minX, y: boxPx.minY)
                let bottomRightPx = CGPoint(x: boxPx.maxX, y: boxPx.maxY)
                let topLeftLocal = geometry.windowLocalPoint(fromCapturePixel: CapturePixelPoint(topLeftPx))
                let bottomRightLocal = geometry.windowLocalPoint(fromCapturePixel: CapturePixelPoint(bottomRightPx))
                let boxLocal = CGRect(
                    x: min(topLeftLocal.x, bottomRightLocal.x),
                    y: min(topLeftLocal.y, bottomRightLocal.y),
                    width: abs(bottomRightLocal.x - topLeftLocal.x),
                    height: abs(bottomRightLocal.y - topLeftLocal.y)
                )
                rowBoxes.append(arrayFromRect(boxLocal))
                let center = CGPoint(x: boxLocal.midX, y: boxLocal.midY)
                safePoints.append(pointArray(center))
                _ = CaptureGeometryRules.isDispatchable(point: WindowLocalPoint(center), safeRect: boxLocal, minimumMarginPt: 1.0)
            }
        }

        func maxCornerDeviation(_ rects: [[Double]]) -> Double {
            guard let first = rects.first else { return 0 }
            var maxDelta = 0.0
            for rect in rects {
                for index in 0..<4 {
                    maxDelta = max(maxDelta, abs(rect[index] - first[index]))
                }
            }
            return maxDelta
        }
        let rowDeviation = maxCornerDeviation(rowBoxes)
        let safeDeviation = maxCornerDeviation(safePoints.map { [$0[0], $0[1], 0, 0] })
        var safeInteriorDispatchable = false
        if let box = rowBoxes.first, box.count == 4 {
            let rect = CGRect(x: box[0], y: box[1], width: box[2], height: box[3])
            let center = WindowLocalPoint(x: rect.midX, y: rect.midY)
            safeInteriorDispatchable = CaptureGeometryRules.isDispatchable(point: center, safeRect: rect, minimumMarginPt: 1.0)
        }

        // 禎/楨 discriminator fixture on real captures.
        _ = try await harnessCall("setTitle", params: ["title": "旻謙允楨成長日記"])
        await waitForSettle(0.8)
        var otherFound = false
        var expectedAbsent = true
        do {
            let content = try await freshContent()
            if let main = harnessMainWindow(in: content) {
                let image = try await RawCapture.capture(window: main, configuration: configuration(includeChild: false, ignoreShadows: true))
                let items = try await ocr.recognize(image: image)
                otherFound = !OcrTextIdentity.exactMatches(in: items, expected: "旻謙允楨成長日記").isEmpty
                expectedAbsent = OcrTextIdentity.exactMatches(in: items, expected: "旻謙允禎成長日記").isEmpty
            }
        }
        _ = try await harnessCall("setTitle", params: ["title": "旻謙允禎成長日記"])
        await waitForSettle(0.8)
        var expectedRestored = false
        do {
            let content = try await freshContent()
            if let main = harnessMainWindow(in: content) {
                let image = try await RawCapture.capture(window: main, configuration: configuration(includeChild: false, ignoreShadows: true))
                let items = try await ocr.recognize(image: image)
                expectedRestored = !OcrTextIdentity.exactMatches(in: items, expected: "旻謙允禎成長日記").isEmpty
            }
        }

        // Ambiguity fixture: two identical menu rows must refuse.
        let ambiguousRows = ["選擇項目", "儲存全部", "儲存全部", "刪除相簿", "分享相簿"]
        _ = try await harnessCall("setMenuRows", params: ["rows": ambiguousRows])
        await waitForSettle(0.8)
        var ambiguityMatchCount = 0
        do {
            let content = try await freshContent()
            if let main = harnessMainWindow(in: content) {
                let image = try await RawCapture.capture(window: main, configuration: configuration(includeChild: false, ignoreShadows: true))
                let items = try await ocr.recognize(image: image)
                ambiguityMatchCount = OcrTextIdentity.exactMatches(in: items, expected: "儲存全部").count
            }
        }
        _ = try await harnessCall("setMenuRows", params: ["rows": defaultRows])

        let record = VisionLocalizationRecord(
            titleFixture: "旻謙允禎成長日記",
            otherTitleFixture: "旻謙允楨成長日記",
            countFixture: "57張照片",
            menuRows: defaultRows,
            recognizedStrings: recognized,
            exactMenuRowMatch: rowMatchCount == 1,
            exactMenuRowMatchCount: rowMatchCount,
            exactCountMatch: countMatch,
            exactTitleMatch: titleMatch,
            rowBoxesLocalPtAcrossCaptures: rowBoxes,
            rowBoxMaxCornerDeviationPt: rowDeviation,
            safePointsLocalPtAcrossCaptures: safePoints,
            safePointMaxDeviationPt: safeDeviation,
            safeInteriorDispatchable: safeInteriorDispatchable,
            discriminatorOtherTitleFound: otherFound,
            discriminatorExpectedTitleAbsentWithOtherLabel: expectedAbsent,
            discriminatorExpectedTitleFoundAfterRestore: expectedRestored,
            ambiguityMenuRows: ambiguousRows,
            ambiguityMatchCount: ambiguityMatchCount,
            ambiguityRefused: ambiguityMatchCount != 1,
            atISO8601: EvidenceIO.iso8601()
        )
        let pass = record.exactMenuRowMatch && record.exactCountMatch && record.exactTitleMatch
            && safeInteriorDispatchable && otherFound && expectedAbsent && expectedRestored
            && record.ambiguityRefused && rowBoxes.count >= 2
        let verdict = pass ? "PASS" : "PARTIAL"
        let detail = "menuRowMatches=\(rowMatchCount) countMatch=\(countMatch) titleMatch=\(titleMatch) rowBoxDeviation=\(rowDeviation) safePointDeviation=\(safeDeviation) 楨Found=\(otherFound) ambiguityMatches=\(ambiguityMatchCount)"
        try await recordItem(2, name: "vision-localization", verdict: verdict, detail: detail, fileName: "02-vision-localization.json", value: record)
    }

    // MARK: - Item 3: coordinate transforms

    private func item03Transforms() async throws {
        guard let ruleBook = frozenRuleBook else {
            try await recordItem(3, name: "coordinate-transforms", verdict: "NOT_RUN", detail: "frozen rule book unavailable (item 1 must run first)", fileName: "03-coordinate-transforms.json", value: ["detail": "frozen rule book unavailable"])
            return
        }
        _ = try await harnessCall("hidePopup")
        _ = try await harnessCall("setShadows", params: ["on": true])
        _ = try await harnessCall("activate")
        await waitForSettle(0.8)
        try await refreshHarnessState()

        let state = CaptureGeometryState(settled: true, activated: harnessActive(), includeChildWindows: false, ignoreShadows: true)
        let cfg = configuration(includeChild: false, ignoreShadows: true)
        let content = try await freshContent()
        guard let main = harnessMainWindow(in: content) else {
            throw NSError(domain: "rev28ctl", code: 7, userInfo: [NSLocalizedDescriptionKey: "harness main window not found"])
        }
        let snapshots = harnessSnapshots(in: content).filter { $0.windowID == main.windowID }
        let service = FrameCaptureService(ruleBook: ruleBook)
        let record = try await service.capture(window: main, configuration: cfg, includedWindows: snapshots, state: state, identityTemplate: nil)
        guard record.validity == .valid else {
            try await recordItem(3, name: "coordinate-transforms", verdict: "PARTIAL", detail: "capture invalid: \(record.violations)", fileName: "03-coordinate-transforms.json", value: ["violations": record.violations])
            return
        }
        let geometry = CaptureGeometry(windowFrame: main.frame, captureBBox: record.actualBBoxPt, scale: record.scale)
        let startFrame = main.frame

        guard let rowRects = harnessState["menuRowRectsLocalTopLeft"] as? [[String: Any]],
              let rowRect = dictRect(rowRects.count > 2 ? rowRects[2] : rowRects.first) else {
            throw NSError(domain: "rev28ctl", code: 8, userInfo: [NSLocalizedDescriptionKey: "menu row rects unavailable"])
        }
        let local = WindowLocalPoint(x: Double(rowRect.midX), y: Double(rowRect.midY))

        var localToScreenMaxError = 0.0
        var localToPixelToLocalMaxError = 0.0
        var pixelToScreenToPixelMaxError = 0.0
        for offset in [WindowLocalPoint(x: 0, y: 0), WindowLocalPoint(x: 1.25, y: -0.75), local] {
            let screen = geometry.screenPoint(fromWindowLocal: offset)
            let backLocal = geometry.windowLocalPoint(fromScreen: screen)
            localToScreenMaxError = max(localToScreenMaxError, abs(backLocal.x - offset.x), abs(backLocal.y - offset.y))
            let pixel = geometry.capturePixelPoint(fromWindowLocal: offset)
            let viaPixelLocal = geometry.windowLocalPoint(fromCapturePixel: pixel)
            localToPixelToLocalMaxError = max(localToPixelToLocalMaxError, abs(viaPixelLocal.x - offset.x), abs(viaPixelLocal.y - offset.y))
            let viaScreen = geometry.screenPoint(fromCapturePixel: pixel)
            let pixelAgain = geometry.capturePixelPoint(fromScreen: viaScreen)
            pixelToScreenToPixelMaxError = max(pixelToScreenToPixelMaxError, abs(pixelAgain.x - pixel.x), abs(pixelAgain.y - pixel.y))
        }

        let screenBefore = geometry.screenPoint(fromWindowLocal: local)
        _ = try await harnessCall("moveBy", params: ["dx": 80.0, "dy": 40.0])
        await waitForSettle(1.2)
        try await refreshHarnessState()
        let contentAfterPositiveMove = try await freshContent()
        var positiveMoveFrame = startFrame
        var screenAfterPositiveMove: ScreenPoint?
        var positiveMoveError = Double.infinity
        if let movedMain = harnessMainWindow(in: contentAfterPositiveMove) {
            positiveMoveFrame = movedMain.frame
            let movedSnapshots = harnessSnapshots(in: contentAfterPositiveMove).filter { $0.windowID == movedMain.windowID }
            let movedRecord = try await service.capture(window: movedMain, configuration: cfg, includedWindows: movedSnapshots, state: state, identityTemplate: nil)
            if movedRecord.validity == .valid {
                let movedGeometry = CaptureGeometry(windowFrame: movedMain.frame, captureBBox: movedRecord.actualBBoxPt, scale: movedRecord.scale)
                screenAfterPositiveMove = movedGeometry.screenPoint(fromWindowLocal: local)
                if let screenAfterPositiveMove {
                    positiveMoveError = max(
                        abs(screenAfterPositiveMove.x - screenBefore.x - 80.0),
                        abs(screenAfterPositiveMove.y - screenBefore.y - 40.0)
                    )
                }
            }
        }

        _ = try await harnessCall("moveBy", params: ["dx": -80.0, "dy": -40.0])
        await waitForSettle(1.2)
        try await refreshHarnessState()
        let contentAfterNegativeMove = try await freshContent()
        var negativeMoveFrame = positiveMoveFrame
        var negativeMoveError = Double.infinity
        var returnToStartError = Double.infinity
        if let movedMain = harnessMainWindow(in: contentAfterNegativeMove),
           let screenAfterPositiveMove {
            negativeMoveFrame = movedMain.frame
            let movedSnapshots = harnessSnapshots(in: contentAfterNegativeMove).filter { $0.windowID == movedMain.windowID }
            let movedRecord = try await service.capture(window: movedMain, configuration: cfg, includedWindows: movedSnapshots, state: state, identityTemplate: nil)
            if movedRecord.validity == .valid {
                let movedGeometry = CaptureGeometry(windowFrame: movedMain.frame, captureBBox: movedRecord.actualBBoxPt, scale: movedRecord.scale)
                let screenAfterNegativeMove = movedGeometry.screenPoint(fromWindowLocal: local)
                negativeMoveError = max(
                    abs(screenAfterNegativeMove.x - screenAfterPositiveMove.x + 80.0),
                    abs(screenAfterNegativeMove.y - screenAfterPositiveMove.y + 40.0)
                )
                returnToStartError = max(
                    abs(screenAfterNegativeMove.x - screenBefore.x),
                    abs(screenAfterNegativeMove.y - screenBefore.y)
                )
            }
        }
        // Wrong-scale injection: independent backing-scale source + size check.
        let scaleViolation = CaptureGeometryRules.validateScale(pointPixelScale: 1.0, backingScaleFactor: Double(NSScreen.screens.first?.backingScaleFactor ?? 2.0))
        let wrongScaleEvaluation = CaptureGeometryRules.evaluate(
            expectedBBox: record.expectedBBoxPt,
            imageWidthPx: record.imageWidthPx,
            imageHeightPx: record.imageHeightPx,
            scale: record.scale / 2.0,
            ruleBook: ruleBook,
            state: state
        )
        var wrongScaleDetail = "validateScale->\(scaleViolation?.description ?? "none")"
        var wrongScaleDetected = scaleViolation != nil
        if case let .failure(violation) = wrongScaleEvaluation {
            wrongScaleDetected = true
            wrongScaleDetail += "; evaluate(scale/2)->\(violation.description)"
        } else {
            wrongScaleDetail += "; evaluate(scale/2)->unexpectedly valid"
        }

        // Safe-interior 1 pt refusal.
        let nearBoundary = WindowLocalPoint(x: Double(rowRect.minX) + 0.5, y: Double(rowRect.midY))
        let center = WindowLocalPoint(x: Double(rowRect.midX), y: Double(rowRect.midY))
        let boundaryRefused = !CaptureGeometryRules.isDispatchable(point: nearBoundary, safeRect: rowRect, minimumMarginPt: 1.0)
        let centerAllowed = CaptureGeometryRules.isDispatchable(point: center, safeRect: rowRect, minimumMarginPt: 1.0)

        // Recorded bbox drives the transform (compare recorded vs expected bbox marker mapping).
        let origin = contentOriginLocalTopLeft()
        let markerScreen = CGPoint(x: Double(startFrame.minX) + Double(origin.x) + 4.0, y: Double(startFrame.minY) + Double(origin.y) + 4.0)
        let recordedPixel = geometry.capturePixelPoint(fromScreen: ScreenPoint(markerScreen))
        let expectedGeometry = CaptureGeometry(windowFrame: startFrame, captureBBox: record.expectedBBoxPt, scale: record.scale)
        let expectedPixel = expectedGeometry.capturePixelPoint(fromScreen: ScreenPoint(markerScreen))
        let markerObserved = (try? await RawCapture.capture(window: main, configuration: cfg)).flatMap { PixelProbe.findRedSquareTopLeft(in: $0) }
        let recordedError = markerObserved.map { max(abs(recordedPixel.x - Double($0.x)), abs(recordedPixel.y - Double($0.y))) } ?? -1
        let expectedError = markerObserved.map { max(abs(expectedPixel.x - Double($0.x)), abs(expectedPixel.y - Double($0.y))) } ?? -1
        let recordedBBoxDiffers = record.actualBBoxPt != record.expectedBBoxPt
        let recordedBBoxDifferentialObserved = recordedBBoxDiffers
            && recordedError >= 0 && expectedError >= 0 && recordedError < expectedError
        let recordedBBoxObservationDetail = recordedBBoxDiffers
            ? "actual and expected bbox differ; recorded/expected marker error=\(recordedError)/\(expectedError)"
            : "not distinguishable in this capture because actual bbox equals expected bbox; differential unit coverage is CoordinateTransformTests.testCapturePixelConversionUsesRecordedBBox"

        let transformRecord = TransformRecord(
            startFrameTopLeft: arrayFromRect(startFrame),
            positiveMoveFrameTopLeft: arrayFromRect(positiveMoveFrame),
            negativeMoveFrameTopLeft: arrayFromRect(negativeMoveFrame),
            scaleObserved: record.scale,
            backingScaleFactor: record.backingScaleFactor,
            localToScreenMaxErrorPt: localToScreenMaxError,
            localToPixelToLocalMaxErrorPt: localToPixelToLocalMaxError,
            pixelToScreenToPixelMaxErrorPt: pixelToScreenToPixelMaxError,
            screenShiftAfterPositiveMoveErrorPt: positiveMoveError,
            screenShiftAfterNegativeMoveErrorPt: negativeMoveError,
            screenReturnToStartErrorPt: returnToStartError,
            wrongScaleDetected: wrongScaleDetected,
            wrongScaleDetail: wrongScaleDetail,
            safeInteriorRefusalDemonstrated: boundaryRefused && centerAllowed,
            safeInteriorDetail: "boundary+0.5pt refused=\(boundaryRefused); center allowed=\(centerAllowed)",
            recordedBBoxDifferentialObserved: recordedBBoxDifferentialObserved,
            recordedBBoxObservationDetail: recordedBBoxObservationDetail,
            recordedBBoxMarkerErrorPt: recordedError,
            expectedBBoxMarkerErrorPt: expectedError,
            atISO8601: EvidenceIO.iso8601()
        )
        let pass = localToScreenMaxError < 1e-6 && localToPixelToLocalMaxError < 1e-6
            && pixelToScreenToPixelMaxError < 1e-6
            && positiveMoveError < 1.0 && negativeMoveError < 1.0 && returnToStartError < 1.0
            && wrongScaleDetected && transformRecord.safeInteriorRefusalDemonstrated
        let detail = "roundTripMaxError=\(localToScreenMaxError) move(+/-/return)=\(positiveMoveError)/\(negativeMoveError)/\(returnToStartError) wrongScale=\(wrongScaleDetected) safeInterior=\(transformRecord.safeInteriorRefusalDemonstrated) bboxDifferential=\(recordedBBoxDifferentialObserved)"
        try await recordItem(3, name: "coordinate-transforms", verdict: pass ? "PASS" : "PARTIAL", detail: detail, fileName: "03-coordinate-transforms.json", value: transformRecord)
    }

    // MARK: - Item 4: Quartz routing

    private func item04QuartzRouting() async throws {
        _ = try await occluderCall("hide")
        _ = try await harnessCall("hidePopup")
        _ = try await harnessCall("activate")
        _ = try await harnessCall("setShadows", params: ["on": true])
        _ = try await harnessCall("setFrame", params: ["x": 160.0, "y": 140.0, "w": 800.0, "h": 600.0])
        await waitForSettle(1.0)
        _ = try await harnessCall("hitReport", params: ["reset": true])
        _ = try await occluderCall("hitReport", params: ["reset": true])
        _ = try await harnessCall("showPopup", params: ["dx": 120.0, "dy": 80.0])
        await waitForSettle(0.8)
        try await refreshHarnessState()

        guard let popupFrame = dictRect(harnessState["popupFrameTopLeft"]),
              let popupRow = dictRect(harnessState["popupRowRectLocalTopLeft"]) else {
            try await recordItem(4, name: "quartz-routing", verdict: "NOT_RUN", detail: "popup frame unavailable", fileName: "04-quartz-routing.json", value: ["detail": "popupFrame unavailable"])
            return
        }
        let popupPoint = CGPoint(x: popupFrame.minX + popupRow.midX, y: popupFrame.minY + popupRow.midY)
        try QuartzActuator.postClick(at: ScreenPoint(popupPoint))
        inputPostCount += 1
        await sleep(milliseconds: 500)
        let popupHitReport = try await harnessCall("hitReport")
        let popupHitsAfterPopupClick = (popupHitReport["popupHits"] as? NSNumber)?.intValue ?? -1
        let mainHitsAfterPopupClick = (popupHitReport["mainHits"] as? NSNumber)?.intValue ?? -1
        let lastPopupHitLocal = dictPoint(popupHitReport["lastPopupHitLocal"])

        guard let rowRects = harnessState["menuRowRectsLocalTopLeft"] as? [[String: Any]],
              let mainRow = dictRect(rowRects.first),
              let mainFrame = dictRect(harnessState["mainFrameTopLeft"]) else {
            throw NSError(domain: "rev28ctl", code: 9, userInfo: [NSLocalizedDescriptionKey: "main row rects unavailable"])
        }
        let mainPoint = CGPoint(x: mainFrame.minX + mainRow.midX, y: mainFrame.minY + mainRow.midY)
        try QuartzActuator.postClick(at: ScreenPoint(mainPoint))
        inputPostCount += 1
        await sleep(milliseconds: 500)
        let mainHitReport = try await harnessCall("hitReport")
        let mainHitsAfterMainClick = (mainHitReport["mainHits"] as? NSNumber)?.intValue ?? -1
        let popupHitsAfterMainClick = (mainHitReport["popupHits"] as? NSNumber)?.intValue ?? -1
        let lastMainHitLocal = dictPoint(mainHitReport["lastMainHitLocal"])

        // Occluder covers the main window; the main point must hit the occluder.
        let cover = try await occluderCall("cover", params: ["x": Double(mainFrame.origin.x), "y": Double(mainFrame.origin.y), "w": Double(mainFrame.width), "h": Double(mainFrame.height), "activate": true])
        await waitForSettle(0.7)
        let coverFrame = dictRect(cover["frameTopLeft"]) ?? mainFrame
        try QuartzActuator.postClick(at: ScreenPoint(mainPoint))
        inputPostCount += 1
        await sleep(milliseconds: 500)
        let coveredMainReport = try await harnessCall("hitReport")
        let occluderHitReport = try await occluderCall("state")
        let coverHitsAfterCoveredMainClick = (occluderHitReport["coverHits"] as? NSNumber)?.intValue ?? -1
        let mainHitsAfterCoveredMainClick = (coveredMainReport["mainHits"] as? NSNumber)?.intValue ?? -1
        let lastCoverHitLocal = dictPoint(occluderHitReport["lastCoverHitLocal"])

        // Reorder and freshly bind the popup after the peer occluder becomes
        // active. The previous popup coordinate/z-order is stale after that
        // surface transition and cannot authorize this routing probe.
        _ = try await harnessCall("showPopup", params: ["dx": 120.0, "dy": 80.0])
        await waitForSettle(0.6)
        try await refreshHarnessState()
        guard let raisedPopupFrame = dictRect(harnessState["popupFrameTopLeft"]),
              let raisedPopupRow = dictRect(harnessState["popupRowRectLocalTopLeft"]) else {
            try await recordItem(4, name: "quartz-routing", verdict: "PARTIAL", detail: "popup could not be freshly rebound after occluder activation", fileName: "04-quartz-routing.json", value: ["popupRebound": false])
            return
        }
        let raisedPopupPoint = CGPoint(x: raisedPopupFrame.minX + raisedPopupRow.midX, y: raisedPopupFrame.minY + raisedPopupRow.midY)
        let raisedContent = try await freshContent()
        let raisedPopupVisible = popupWindow(in: raisedContent)?.isOnScreen == true
        let occluderBeforePopupClick = try await occluderCall("state")
        let harnessActiveAtCoveredPopupClick = harnessActive()
        let occluderActiveAtCoveredPopupClick = (occluderBeforePopupClick["active"] as? Bool) ?? false
        let occluderCoverVisibleAtCoveredPopupClick = (occluderBeforePopupClick["coverVisible"] as? Bool) ?? false
        // App activation flags are recorded as diagnostics only. The planned
        // proof is about actual Quartz routing with both windows visible, so
        // the event counters below decide whether the popup was topmost.
        guard raisedPopupVisible, occluderCoverVisibleAtCoveredPopupClick else {
            try await recordItem(4, name: "quartz-routing", verdict: "PARTIAL", detail: "raised popup or visible occluder cover precondition missing", fileName: "04-quartz-routing.json", value: ["popupVisible": raisedPopupVisible, "coverVisible": occluderCoverVisibleAtCoveredPopupClick])
            return
        }

        // The popup must be topmost while the separate-process occluder remains
        // active and visibly covers the main window.
        try QuartzActuator.postClick(at: ScreenPoint(raisedPopupPoint))
        inputPostCount += 1
        await sleep(milliseconds: 500)
        let coveredPopupReport = try await harnessCall("hitReport")
        let occluderAfterPopup = try await occluderCall("state")
        let popupHitsAfterCoveredPopupClick = (coveredPopupReport["popupHits"] as? NSNumber)?.intValue ?? -1
        let mainHitsAfterCoveredPopupClick = (coveredPopupReport["mainHits"] as? NSNumber)?.intValue ?? -1
        let coverHitsAfterCoveredPopupClick = (occluderAfterPopup["coverHits"] as? NSNumber)?.intValue ?? -1

        _ = try await occluderCall("hide")
        _ = try await harnessCall("activate")
        _ = try await harnessCall("hidePopup")

        let popupReceives = popupHitsAfterPopupClick >= 1 && mainHitsAfterPopupClick == 0
        let mainReceives = mainHitsAfterMainClick >= 1
        let occluderOccludes = coverHitsAfterCoveredMainClick >= 1 && mainHitsAfterCoveredMainClick == mainHitsAfterMainClick
        let popupTopmost = popupHitsAfterCoveredPopupClick == popupHitsAfterMainClick + 1
            && mainHitsAfterCoveredPopupClick == mainHitsAfterMainClick
            && coverHitsAfterCoveredPopupClick == coverHitsAfterCoveredMainClick

        let record = RoutingRecord(
            popupFrameTopLeft: arrayFromRect(popupFrame),
            popupRowPointScreen: pointArray(popupPoint),
            popupFrameRaisedAfterOccluderTopLeft: arrayFromRect(raisedPopupFrame),
            popupRowPointAfterOccluderScreen: pointArray(raisedPopupPoint),
            popupHitsAfterPopupClick: popupHitsAfterPopupClick,
            mainHitsAfterPopupClick: mainHitsAfterPopupClick,
            lastPopupHitLocal: lastPopupHitLocal.map { pointArray($0) },
            mainRowPointScreen: pointArray(mainPoint),
            mainHitsAfterMainClick: mainHitsAfterMainClick,
            popupHitsAfterMainClick: popupHitsAfterMainClick,
            lastMainHitLocal: lastMainHitLocal.map { pointArray($0) },
            occluderCoverFrameTopLeft: arrayFromRect(coverFrame),
            occluderCoverHitsAfterCoveredMainClick: coverHitsAfterCoveredMainClick,
            mainHitsAfterCoveredMainClick: mainHitsAfterCoveredMainClick,
            lastCoverHitLocal: lastCoverHitLocal.map { pointArray($0) },
            popupHitsAfterCoveredPopupClick: popupHitsAfterCoveredPopupClick,
            mainHitsAfterCoveredPopupClick: mainHitsAfterCoveredPopupClick,
            occluderCoverHitsAfterCoveredPopupClick: coverHitsAfterCoveredPopupClick,
            harnessActiveAtCoveredPopupClick: harnessActiveAtCoveredPopupClick,
            occluderActiveAtCoveredPopupClick: occluderActiveAtCoveredPopupClick,
            occluderCoverVisibleAtCoveredPopupClick: occluderCoverVisibleAtCoveredPopupClick,
            popupTopmostOverOccluderProved: popupTopmost,
            popupReceivesEventProved: popupReceives,
            mainWindowNotReceivingPopupEventProved: mainHitsAfterPopupClick == 0,
            occluderOccludesMainWindowProved: occluderOccludes,
            atISO8601: EvidenceIO.iso8601()
        )
        let pass = popupReceives && mainReceives && occluderOccludes && popupTopmost
        let detail = "popupHits=\(popupHitsAfterPopupClick) mainHitsAtPopup=\(mainHitsAfterPopupClick) coverHits=\(coverHitsAfterCoveredMainClick) popupTopmost=\(popupTopmost)"
        try await recordItem(4, name: "quartz-routing", verdict: pass ? "PASS" : "PARTIAL", detail: detail, fileName: "04-quartz-routing.json", value: record)
    }

    // MARK: - Item 6: AX chooser observation + predicate freeze

    private func item06ChooserPredicate() async throws {
        _ = try await occluderCall("hide")
        _ = try await harnessCall("activate")
        _ = try await harnessCall("hidePopup")
        _ = try await harnessCall("setFrame", params: ["x": 160.0, "y": 140.0, "w": 800.0, "h": 600.0])
        await waitForSettle(1.0)

        let destination = run.fixturesDir.appendingPathComponent("panel-destination")
        let startDirectory = run.fixturesDir.appendingPathComponent("panel-start")
        try EvidenceIO.ensureDirectory(destination)
        try EvidenceIO.ensureDirectory(startDirectory)
        let markerName = "rev28-panel-commit.marker"
        let markerURL = destination.appendingPathComponent(markerName)

        let preCensus = try await onScreenWindowOwnerPIDs()
        let preWindowIDs = Set(try await freshContent().windows.map { $0.windowID })

        _ = try await harnessCall("showPanel", params: ["delayMs": 0, "directory": startDirectory.path, "marker": markerName, "expectedDirectory": destination.path])
        _ = await harness.waitForEvent("panelWillShow", timeoutSeconds: 8)
        let shownEvent = await harness.waitForEvent("panelShown", timeoutSeconds: 8)
        let panelShownAt = (shownEvent?["at"] as? NSNumber)?.doubleValue
        let panelKeyAtShown = (shownEvent?["keyWindow"] as? NSNumber)?.boolValue ?? false
        let appActiveAtShown = (shownEvent?["appActive"] as? NSNumber)?.boolValue ?? false

        let pid = harnessPID()
        guard let panelElement = panelWindowElement(pid: pid), panelShownAt != nil else {
            try await recordItem(6, name: "chooser-predicate-freeze", verdict: "NOT_RUN", detail: "real NSOpenPanel window not observed (panelShown=\(panelShownAt != nil))", fileName: "06-chooser-predicate.json", value: ["detail": "panel window not observed"])
            return
        }
        let panelRole = AXDriver.role(of: panelElement)
        let panelSubrole = AXDriver.subrole(of: panelElement)
        let panelTitle = AXDriver.title(of: panelElement)
        let panelFrame = AXDriver.frame(of: panelElement)
        let panelTree = AXDriver.dump(element: panelElement, pid: pid, maxDepth: 10, maxNodes: 1500)
        let nodes = panelTree.nodes
        let buttons = nodes.filter { $0.role == "AXButton" }
        let textFields = nodes.filter { $0.role == "AXTextField" }
        let popUps = nodes.filter { ($0.role == "AXPopUpButton" || $0.role == "AXComboBox") }
        let defaultButton = buttons.first { ($0.keyEquivalent ?? $0.attributes["AXKeyEquivalent"]) == "\r" }
        let cancelButton = buttons.first { ($0.title ?? $0.description ?? "") == "取消" }
        var pathCandidates: [String] = []
        for node in nodes where node.role == "AXTextField" || node.role == "AXPopUpButton" || node.role == "AXComboBox" {
            if let value = node.value, value.contains("/") { pathCandidates.append(value) }
            if let title = node.title, title.contains("/") { pathCandidates.append(title) }
        }

        let defaultRequirement: ButtonRequirement? = {
            if let button = defaultButton, let keyEquivalent = button.keyEquivalent ?? button.attributes["AXKeyEquivalent"] {
                return ButtonRequirement(mode: .attributeEquals, attributeName: "AXKeyEquivalent", attributeValue: keyEquivalent, titles: [], buttonRoles: ["AXButton"])
            }
            if let title = defaultButton?.title ?? defaultButton?.description {
                return ButtonRequirement(mode: .titleIn, attributeName: nil, attributeValue: nil, titles: [title], buttonRoles: ["AXButton"])
            }
            return nil
        }()
        let cancelRequirement: ButtonRequirement? = {
            guard let title = cancelButton?.title ?? cancelButton?.description else { return nil }
            return ButtonRequirement(mode: .titleIn, attributeName: nil, attributeValue: nil, titles: [title], buttonRoles: ["AXButton"])
        }()
        let textFieldRoles = Array(Set(textFields.compactMap { $0.role })).sorted()
        let popUpRoles = Array(Set(popUps.compactMap { $0.role })).sorted()

        let predicate = ChooserAffirmationPredicate(
            predicateID: "rev28-chooser-affirmation-v1",
            frozenAtISO8601: EvidenceIO.iso8601(),
            calibratedAgainst: "real NSOpenPanel (directory mode) presented by rev28harness pid \(pid) on \(ProcessInfo.processInfo.operatingSystemVersionString)",
            ax: ChooserAXClauseSet(
                windowRole: panelRole ?? "AXWindow",
                allowedSubroles: panelSubrole.map { [$0] } ?? [],
                requiresTextField: !textFields.isEmpty,
                textFieldRoles: textFieldRoles,
                requiresPopUpButton: !popUps.isEmpty,
                popUpButtonRoles: popUpRoles,
                defaultButton: defaultRequirement,
                cancelButton: cancelRequirement,
                requiresPathAffordance: !textFields.isEmpty,
                pathAffordanceRoles: textFieldRoles,
                pathAffordanceTitles: []
            ),
            ownership: ChooserOwnershipClauseSet(
                requiresOwningPIDInCensusUnion: true,
                requiresStableProcessInstance: true,
                emptyPreCensusWidensRefusal: true
            )
        )
        frozenPredicate = predicate

        let calibration = ChooserAxCalibrationRecord(
            harnessPID: pid,
            harnessOwnedSCWindows: [],
            panelWindowFound: true,
            panelWindowRole: panelRole,
            panelWindowSubrole: panelSubrole,
            panelWindowTitle: panelTitle,
            panelWindowFramePt: panelFrame.map { arrayFromRect($0) },
            axNodeCount: nodes.count,
            rolesObserved: Array(Set(nodes.compactMap { $0.role })).sorted(),
            subrolesObserved: Array(Set(nodes.compactMap { $0.subrole })).sorted(),
            buttonTitles: buttons.map { $0.title ?? $0.description ?? "?" },
            defaultButtonTitle: defaultButton?.title ?? defaultButton?.description,
            defaultButtonKeyEquivalent: defaultButton?.keyEquivalent ?? defaultButton?.attributes["AXKeyEquivalent"],
            textFieldRoles: textFieldRoles,
            popUpRoles: popUpRoles,
            pathValueCandidates: Array(Set(pathCandidates)).sorted(),
            axDumpNodeCount: panelTree.nodeCount,
            atISO8601: EvidenceIO.iso8601()
        )
        try await recordItem(6, name: "chooser-ax-calibration", verdict: "PASS", detail: "panel role=\(panelRole ?? "?") subrole=\(panelSubrole ?? "?") nodes=\(nodes.count) defaultButton=\(defaultButton?.title ?? defaultButton?.description ?? "?")", fileName: "06-chooser-ax-calibration.json", value: calibration)

        // Proofs against the frozen predicate.
        let postCensus = try await onScreenWindowOwnerPIDs()
        var proof = ChooserPredicateProofRecord(
            predicateID: predicate.predicateID,
            realPanelVerdict: "notEvaluated",
            realPanelDetail: "",
            fakeSameProcessVerdict: "notEvaluated",
            fakeSameProcessCause: "",
            fakeSameProcessDetail: "",
            emptyCensusFakeVerdict: "notEvaluated",
            emptyCensusFakeCause: "",
            occluderLookAlikeVerdict: "notEvaluated",
            occluderLookAlikeCause: "",
            ownershipUnboundVerdict: "notEvaluated",
            ownershipUnboundCause: "",
            pidReuseVerdict: "notEvaluated",
            pidReuseCause: "",
            notNewVerdict: "notEvaluated",
            notNewCause: "",
            navigationReflected: false,
            navigationCandidatesAfter: [],
            panelDirectoryAfterNavigation: nil,
            pressedButtonDescription: nil,
            confirmationAction: "none",
            panelClosedResponse: nil,
            confirmedDirectory: nil,
            markerPath: nil,
            markerVerified: false,
            inputPostsDuringFixture: 0,
            atISO8601: EvidenceIO.iso8601()
        )

        func verdictDescription(_ verdict: ChooserPredicateVerdict) -> (String, String, String) {
            switch verdict {
            case .affirmed:
                return ("affirmed", "", "")
            case let .refused(cause, detail):
                return ("refused", cause.rawValue, detail)
            }
        }

        if let candidate = try await chooserCandidate(
            ownerPID: pid,
            matchFrame: panelFrame,
            preCensus: preCensus,
            postCensus: postCensus,
            preDispatchWindowIDs: preWindowIDs,
            isNew: true,
            pidReuseDetected: false
        ) {
            let evaluated = ChooserAffirmationEvaluator.evaluate(candidate: candidate, predicate: predicate)
            let described = verdictDescription(evaluated)
            proof.realPanelVerdict = described.0
            proof.realPanelDetail = "keyWindowAtShown=\(panelKeyAtShown) appActiveAtShown=\(appActiveAtShown)"
            if !described.2.isEmpty { proof.realPanelDetail += "; \(described.2)" }

            // Ownership-unbound and pid-reuse clause proofs on the real surface.
            let unbound = ChooserAffirmationEvaluator.evaluate(
                candidate: rebuildCandidate(candidate, preCensus: [99999], postCensus: [99999]),
                predicate: predicate
            )
            let unboundDescribed = verdictDescription(unbound)
            proof.ownershipUnboundVerdict = unboundDescribed.0
            proof.ownershipUnboundCause = unboundDescribed.1
            let reused = ChooserAffirmationEvaluator.evaluate(
                candidate: rebuildCandidate(candidate, pidReuse: true),
                predicate: predicate
            )
            let reusedDescribed = verdictDescription(reused)
            proof.pidReuseVerdict = reusedDescribed.0
            proof.pidReuseCause = reusedDescribed.1
            let notNew = ChooserAffirmationEvaluator.evaluate(
                candidate: rebuildCandidate(candidate, isNew: false),
                predicate: predicate
            )
            let notNewDescribed = verdictDescription(notNew)
            proof.notNewVerdict = notNewDescribed.0
            proof.notNewCause = notNewDescribed.1
        }

        // Navigation: the keyboard shortcut opens the path field; the shared
        // chooser driver replaces its value and verifies the requested path.
        do {
            let focus = try await harnessCall("focusPanel")
            let panelIsActive = (focus["active"] as? NSNumber)?.boolValue ?? false
            let panelIsKey = (focus["keyWindow"] as? NSNumber)?.boolValue ?? false
            proof.realPanelDetail += "; navigationFocus active=\(panelIsActive) keyWindow=\(panelIsKey)"
            guard panelIsActive && panelIsKey else {
                throw NSError(domain: "rev28ctl", code: 6, userInfo: [NSLocalizedDescriptionKey: "harness chooser did not become the active key window"])
            }
            await sleep(milliseconds: 150)
            proof.navigationCandidatesAfter = try FolderChooserDriver.navigateToDestination(pid: pid, destination: destination)
            proof.navigationReflected = true
        } catch {
            proof.navigationCandidatesAfter = FolderChooserDriver.directoryCandidates(pid: pid)
            proof.realPanelDetail += "; navigationDriverError=\(error)"
        }
        inputPostCount += 3
        await sleep(milliseconds: 900)
        let panelStateAfterNavigation = try await harnessCall("state")
        let panelDirectoryAfterNavigation = (panelStateAfterNavigation["panelDirectory"] as? String)
            .map { URL(fileURLWithPath: $0).standardizedFileURL.path }
        proof.panelDirectoryAfterNavigation = panelDirectoryAfterNavigation
        proof.navigationReflected = proof.navigationReflected
            || panelDirectoryAfterNavigation == destination.standardizedFileURL.path
            || FolderChooserDriver.destinationIsReflected(pid: pid, destination: destination)

        guard proof.navigationReflected else {
            proof.confirmationAction = "notAttemptedDestinationNotReflected"
            proof.markerPath = markerURL.path
            proof.inputPostsDuringFixture = inputPostCount
            proof.atISO8601 = EvidenceIO.iso8601()
            _ = try await harnessCall("closePanel")
            let cancelledEvent = await harness.waitForEvent("panelClosed", timeoutSeconds: 6)
            proof.panelClosedResponse = (cancelledEvent?["response"] as? NSNumber)?.intValue
            try await recordItem(6, name: "chooser-predicate-proof", verdict: "PARTIAL", detail: "destination was not reflected; confirmation was withheld", fileName: "06-chooser-predicate-proof.json", value: proof)
            return
        }

        guard FolderChooserDriver.defaultButton(pid: pid, titles: ["開啟", "Open", "打開"]) != nil else {
            proof.confirmationAction = "notAttemptedDefaultButtonMissing"
            proof.panelClosedResponse = nil
            proof.markerPath = markerURL.path
            proof.inputPostsDuringFixture = inputPostCount
            proof.atISO8601 = EvidenceIO.iso8601()
            _ = try await harnessCall("closePanel")
            let cancelledEvent = await harness.waitForEvent("panelClosed", timeoutSeconds: 6)
            proof.panelClosedResponse = (cancelledEvent?["response"] as? NSNumber)?.intValue
            try await recordItem(6, name: "chooser-predicate-proof", verdict: "PARTIAL", detail: "Go-to-folder navigation did not restore the panel's confirmation control; navigationReflected=\(proof.navigationReflected)", fileName: "06-chooser-predicate-proof.json", value: proof)
            return
        }

        // Confirmation: exactly one action chosen (AXPress on the default button).
        let pressedDescription = try FolderChooserDriver.pressDefaultButton(pid: pid, titles: ["開啟", "Open", "打開"])
        proof.pressedButtonDescription = pressedDescription
        proof.confirmationAction = ChooserConfirmationAction.axPressDefaultButton.rawValue
        inputPostCount += 1
        let closedEvent = await harness.waitForEvent("panelClosed", timeoutSeconds: 10)
        proof.panelClosedResponse = (closedEvent?["response"] as? NSNumber)?.intValue
        proof.confirmedDirectory = closedEvent?["chosenDirectory"] as? String
        proof.markerPath = markerURL.path
        let markerAttributes = try? FileManager.default.attributesOfItem(atPath: markerURL.path)
        let markerSize = (markerAttributes?[.size] as? NSNumber)?.intValue ?? 0
        proof.markerVerified = (closedEvent?["markerPath"] as? String) == markerURL.path
            && FileManager.default.fileExists(atPath: markerURL.path) && markerSize > 0
        proof.inputPostsDuringFixture = inputPostCount
        proof.atISO8601 = EvidenceIO.iso8601()

        // Ambiguity/look-alike refusals: same-process fake chooser.
        _ = try await harnessCall("closePanel").self
        _ = await harness.waitForEvent("panelClosed", timeoutSeconds: 4)
        _ = try await harnessCall("showFakeChooser", params: ["dx": 80.0, "dy": 80.0])
        await waitForSettle(0.8)
        let fakeCensus = try await onScreenWindowOwnerPIDs()
        if let fake = try await chooserCandidate(
            ownerPID: pid,
            matchFrame: nil,
            windowTitle: "Open",
            preCensus: fakeCensus,
            postCensus: fakeCensus,
            preDispatchWindowIDs: preWindowIDs,
            isNew: true,
            pidReuseDetected: false
        ) {
            let described = verdictDescription(ChooserAffirmationEvaluator.evaluate(candidate: fake, predicate: predicate))
            proof.fakeSameProcessVerdict = described.0
            proof.fakeSameProcessCause = described.1
            proof.fakeSameProcessDetail = described.2
            let emptyCensusDescribed = verdictDescription(ChooserAffirmationEvaluator.evaluate(
                candidate: rebuildCandidate(fake, preCensus: [], postCensus: fakeCensus),
                predicate: predicate
            ))
            proof.emptyCensusFakeVerdict = emptyCensusDescribed.0
            proof.emptyCensusFakeCause = emptyCensusDescribed.1
        }
        _ = try await harnessCall("hideFakeChooser")

        // Look-alike owned by a different process (rev28occluder).
        let occluderPID = occluder.process.processIdentifier
        _ = try await occluderCall("lookalike", params: ["x": 700.0, "y": 120.0, "w": 420.0, "h": 220.0])
        await waitForSettle(0.8)
        if let lookAlike = try await chooserCandidate(
            ownerPID: occluderPID,
            matchFrame: nil,
            windowTitle: "Open",
            preCensus: fakeCensus + [occluderPID],
            postCensus: fakeCensus + [occluderPID],
            preDispatchWindowIDs: preWindowIDs,
            isNew: true,
            pidReuseDetected: false
        ) {
            let described = verdictDescription(ChooserAffirmationEvaluator.evaluate(candidate: lookAlike, predicate: predicate))
            proof.occluderLookAlikeVerdict = described.0
            proof.occluderLookAlikeCause = described.1
        }
        _ = try await occluderCall("hideLookalike")

        let pass = proof.realPanelVerdict == "affirmed"
            && proof.fakeSameProcessVerdict == "refused"
            && proof.emptyCensusFakeVerdict == "refused"
            && proof.occluderLookAlikeVerdict == "refused"
            && proof.ownershipUnboundCause == "ownershipUnbound"
            && proof.pidReuseCause == "pidReuse"
            && proof.notNewCause == "notNewWindow"
            && proof.navigationReflected
            && proof.confirmedDirectory == destination.standardizedFileURL.path
            && proof.markerVerified
        let detail = "realPanel=\(proof.realPanelVerdict) fakeSame=\(proof.fakeSameProcessVerdict)/\(proof.fakeSameProcessCause) emptyCensus=\(proof.emptyCensusFakeVerdict) occluderLookAlike=\(proof.occluderLookAlikeVerdict)/\(proof.occluderLookAlikeCause) nav=\(proof.navigationReflected) marker=\(proof.markerVerified)"
        try await recordItem(6, name: "chooser-predicate-proof", verdict: pass ? "PASS" : "PARTIAL", detail: detail, fileName: "06-chooser-predicate-proof.json", value: proof)
        // Only a validated predicate is frozen: a partial proof (e.g. the real
        // panel refused because the harness presented it as a sheet rather than
        // a standalone window) is evidence, never a canonical freeze.
        if pass {
            try recordFrozen("chooser-affirmation-predicate-v2.json", value: predicate)
            try recordFrozen("chooser-ax-calibration-v2.json", value: calibration)
        } else {
            notes.append("NOT_FROZEN: chooser-affirmation-predicate-v2.json and chooser-ax-calibration-v2.json were NOT written to the canonical frozen/ dir (proof verdict PARTIAL: realPanel=\(proof.realPanelVerdict) nav=\(proof.navigationReflected))")
        }
    }

    private func rebuildCandidate(
        _ candidate: ChooserCandidate,
        preCensus: [Int32]? = nil,
        postCensus: [Int32]? = nil,
        pidReuse: Bool? = nil,
        isNew: Bool? = nil
    ) -> ChooserCandidate {
        ChooserCandidate(
            windowID: candidate.windowID,
            frame: candidate.frame,
            onScreen: candidate.onScreen,
            presentInSCInventory: candidate.presentInSCInventory,
            presentInCGInventory: candidate.presentInCGInventory,
            isNewRelativeToPreDispatchInventory: isNew ?? candidate.isNewRelativeToPreDispatchInventory,
            owner: candidate.owner,
            pidReuseDetected: pidReuse ?? candidate.pidReuseDetected,
            axNodes: candidate.axNodes,
            preDispatchCensusPIDs: preCensus ?? candidate.preDispatchCensusPIDs,
            postDispatchCensusPIDs: postCensus ?? candidate.postDispatchCensusPIDs
        )
    }

    private func onScreenWindowOwnerPIDs() async throws -> [Int32] {
        let content = try await freshContent()
        return Array(Set(content.windows.filter { $0.isOnScreen }.compactMap { $0.owningApplication?.processID })).sorted()
    }

    private func panelWindowElement(pid: Int32) -> AXUIElement? {
        for window in AXDriver.windows(ofApp: pid) {
            let hasTextField = AXDriver.firstDescendant(of: window, maxDepth: 8) { element in
                AXDriver.role(of: element) == (kAXTextFieldRole as String)
            } != nil
            let hasButton = AXDriver.firstDescendant(of: window, maxDepth: 8) { element in
                AXDriver.role(of: element) == (kAXButtonRole as String)
            } != nil
            if hasTextField && hasButton { return window }
        }
        return nil
    }

    private func axWindowElement(pid: Int32, matchingFrame frame: CGRect) -> AXUIElement? {
        var best: (element: AXUIElement, distance: Double)?
        for window in AXDriver.windows(ofApp: pid) {
            guard let axFrame = AXDriver.frame(of: window) else { continue }
            let distance = Double(abs(axFrame.minX - frame.minX) + abs(axFrame.minY - frame.minY)
                + abs(axFrame.width - frame.width) + abs(axFrame.height - frame.height))
            if distance <= 6, best == nil || distance < best!.distance {
                best = (window, distance)
            }
        }
        return best?.element
    }

    private func chooserCandidate(
        ownerPID: Int32,
        matchFrame: CGRect?,
        windowTitle: String? = nil,
        preCensus: [Int32],
        postCensus: [Int32],
        preDispatchWindowIDs: Set<UInt32>,
        isNew: Bool,
        pidReuseDetected: Bool
    ) async throws -> ChooserCandidate? {
        let content = try await freshContent()
        let cgInventory = CGWindowInventory.onScreenWindows()
        let owned = content.windows.filter { window in
            guard window.owningApplication?.processID == ownerPID, window.isOnScreen else { return false }
            if let windowTitle, window.title != windowTitle { return false }
            if let matchFrame {
                let distance = abs(window.frame.minX - matchFrame.minX) + abs(window.frame.minY - matchFrame.minY)
                    + abs(window.frame.width - matchFrame.width) + abs(window.frame.height - matchFrame.height)
                if distance > 6 { return false }
            }
            return true
        }
        guard let window = owned.max(by: { $0.frame.width * $0.frame.height < $1.frame.width * $1.frame.height }) else { return nil }
        guard let axElement = axWindowElement(pid: ownerPID, matchingFrame: window.frame) else { return nil }
        let dump = AXDriver.dump(element: axElement, pid: ownerPID, maxDepth: 8, maxNodes: 800)
        let facts = ProcessIdentity.reading(pid: ownerPID)
        let presentInCG = cgInventory.contains { $0.windowNumber == window.windowID }
        return ChooserCandidate(
            windowID: window.windowID,
            frame: window.frame,
            onScreen: window.isOnScreen,
            presentInSCInventory: true,
            presentInCGInventory: presentInCG,
            isNewRelativeToPreDispatchInventory: isNew && !preDispatchWindowIDs.contains(window.windowID),
            owner: facts,
            pidReuseDetected: pidReuseDetected,
            axNodes: dump.nodes,
            preDispatchCensusPIDs: preCensus,
            postDispatchCensusPIDs: postCensus
        )
    }

    // MARK: - Item 5: postcondition detection + bounds freeze

    private func item05Postcondition() async throws {
        _ = try await occluderCall("hide")
        _ = try await harnessCall("activate")
        _ = try await harnessCall("hidePopup")
        _ = try await harnessCall("setFrame", params: ["x": 160.0, "y": 140.0, "w": 800.0, "h": 600.0])
        await waitForSettle(0.8)
        try await refreshHarnessState()

        var samples: [LatencySampleMs] = []
        for index in 1...20 {
            let destination = run.fixturesDir.appendingPathComponent("latency-destination-\(index)")
            try EvidenceIO.ensureDirectory(destination)
            let commandAt = Date().timeIntervalSince1970
            _ = try await harnessCall("showPanel", params: ["delayMs": 0, "directory": destination.path, "marker": "latency-\(index).marker"])
            let willShow = await harness.waitForEvent("panelWillShow", timeoutSeconds: 8)
            let shown = await harness.waitForEvent("panelShown", timeoutSeconds: 8)
            let willShowAt = (willShow?["at"] as? NSNumber)?.doubleValue ?? 0
            let shownAt = (shown?["at"] as? NSNumber)?.doubleValue ?? 0
            samples.append(LatencySampleMs(
                run: index,
                delayMs: 0,
                willShowToShownMs: (shownAt - willShowAt) * 1000.0,
                shownEventAt: shownAt
            ))
            _ = commandAt
            _ = try await harnessCall("closePanel")
            _ = await harness.waitForEvent("panelClosed", timeoutSeconds: 6)
            await sleep(milliseconds: 150)
        }

        // Delayed panel (scheduled appearance) — the dispatch-to-visible latency.
        let delayedDestination = run.fixturesDir.appendingPathComponent("latency-destination-delayed")
        try EvidenceIO.ensureDirectory(delayedDestination)
        let delayedScheduledMs = 900
        let dispatchAt = Date().timeIntervalSince1970
        _ = try await harnessCall("showPanel", params: ["delayMs": Double(delayedScheduledMs), "directory": delayedDestination.path, "marker": "latency-delayed.marker"])
        _ = await harness.waitForEvent("panelWillShow", timeoutSeconds: 8)
        let delayedShown = await harness.waitForEvent("panelShown", timeoutSeconds: 8)
        let delayedShownMs = (((delayedShown?["at"] as? NSNumber)?.doubleValue ?? 0) - dispatchAt) * 1000.0
        _ = try await harnessCall("closePanel")
        _ = await harness.waitForEvent("panelClosed", timeoutSeconds: 6)
        await sleep(milliseconds: 200)

        func percentile(_ values: [Double], _ fraction: Double) -> Double {
            guard !values.isEmpty else { return 0 }
            let sorted = values.sorted()
            let index = Int((Double(sorted.count - 1) * fraction).rounded(.up))
            return sorted[min(max(index, 0), sorted.count - 1)]
        }
        let latencies = samples.map { $0.willShowToShownMs }
        let maxMs = latencies.max() ?? 0
        let medianMs = percentile(latencies, 0.5)
        let p95Ms = percentile(latencies, 0.95)

        let latencyRecord = PostconditionLatencyRecord(
            runCount: samples.count,
            scheduledDelayMs: 0,
            samples: samples,
            maxMs: maxMs,
            medianMs: medianMs,
            p95Ms: p95Ms,
            delayedPanelScheduledMs: delayedScheduledMs,
            delayedPanelShownMs: delayedShownMs,
            atISO8601: EvidenceIO.iso8601()
        )
        let latencyWritten = try run.writeItemRecord("05-postcondition-latency.json", latencyRecord)

        let planTimeBounds = PostconditionBounds.planTime
        let frozenBounds = PostconditionBounds(
            fastCadenceMs: planTimeBounds.fastCadenceMs,
            fastPhaseSeconds: planTimeBounds.fastPhaseSeconds,
            slowCadenceMs: planTimeBounds.slowCadenceMs,
            hardCapSeconds: planTimeBounds.hardCapSeconds,
            lateForensicSampleDelaySeconds: planTimeBounds.lateForensicSampleDelaySeconds
        )
        let boundsFreeze = PostconditionBoundsFreeze(
            frozenAtISO8601: EvidenceIO.iso8601(),
            runID: run.runID,
            planTimeBounds: planTimeBounds,
            frozenBounds: frozenBounds,
            measuredRuns: samples.count,
            maxObservedMs: maxMs,
            medianObservedMs: medianMs,
            p95ObservedMs: p95Ms,
            rationale: "max observed real-NSOpenPanel appearance latency \(maxMs) ms and delayed-panel dispatch-to-visible \(delayedShownMs) ms are far below the 8.0 s fast phase; plan-time bounds ≤\(planTimeBounds.fastCadenceMs) ms/\(planTimeBounds.fastPhaseSeconds) s then ≤\(planTimeBounds.slowCadenceMs) ms to hard cap \(planTimeBounds.hardCapSeconds) s are retained unchanged (no silent extension; a later insufficiency is a replan).",
            latencyEvidenceName: "05-postcondition-latency.json",
            latencyEvidenceSHA256: latencyWritten.sha
        )

        guard let predicate = frozenPredicate else {
            try await recordItem(5, name: "postcondition-bounds-freeze", verdict: "NOT_RUN", detail: "frozen chooser predicate unavailable (item 6 must run first)", fileName: "05-postcondition-bounds.json", value: boundsFreeze)
            return
        }

        var proof = PostconditionProofRecord(
            withinWindowOutcome: "notRun",
            withinWindowDetail: "",
            timeoutOutcome: "notRun",
            timeoutDetail: "",
            lateOutcome: "notRun",
            lateDetail: "",
            lateAffirmationNonNil: false,
            lateDiagnosticAffirmed: false,
            lateDiagnosticDetail: "notSampled",
            zeroFurtherInputDuringMonitors: true,
            monitorInputPosts: 0,
            atISO8601: EvidenceIO.iso8601()
        )
        let postMonitorAt = inputPostCount

        // (a) within-window: real panel appears while the monitor observes.
        let withinBounds = PostconditionBounds(fastCadenceMs: 150, fastPhaseSeconds: 8.0, slowCadenceMs: 500, hardCapSeconds: 15.0, lateForensicSampleDelaySeconds: 0.5)
        func makeSamplerContext() async throws -> ChooserSamplerContext {
            let preCensus = try await onScreenWindowOwnerPIDs()
            let preWindowIDs = Set(try await freshContent().windows.map { $0.windowID })
            return ChooserSamplerContext(
                harnessPID: harnessPID(),
                mainWindowID: mainWindowNumber(),
                popupWindowID: popupWindowNumber(),
                predicate: predicate,
                preCensus: preCensus,
                preWindowIDs: preWindowIDs
            )
        }
        let withinSamplerContext = try await makeSamplerContext()
        let withinTask = Task.detached {
            await PostconditionMonitor.run(bounds: withinBounds) {
                await ChooserAffirmationSampler.sample(context: withinSamplerContext)
            }
        }
        await sleep(milliseconds: 250)
        let withinDestination = run.fixturesDir.appendingPathComponent("postcondition-within")
        try EvidenceIO.ensureDirectory(withinDestination)
        _ = try await harnessCall("showPanel", params: ["delayMs": 0, "directory": withinDestination.path, "marker": "within.marker"])
        _ = await harness.waitForEvent("panelShown", timeoutSeconds: 6)
        let withinOutcome = await withinTask.value
        switch withinOutcome {
        case let .chooserVerified(affirmation):
            proof.withinWindowOutcome = "chooserVerified"
            proof.withinWindowDetail = "windowID=\(affirmation.windowID) ownerPID=\(affirmation.ownerPID) predicateID=\(affirmation.predicateID) at=\(affirmation.affirmedAtISO8601)"
        case let .noChooserObserved(count, seconds):
            proof.withinWindowOutcome = "noChooserObserved"
            proof.withinWindowDetail = "samples=\(count) observed=\(seconds)"
        case let .chooserObservedAfterWindow(count, seconds, affirmation):
            proof.withinWindowOutcome = "chooserObservedAfterWindow"
            proof.withinWindowDetail = "samples=\(count) late=\(seconds) affirmed=\(affirmation != nil)"
        }
        _ = try? await harnessCall("closePanel")
        _ = await harness.waitForEvent("panelClosed", timeoutSeconds: 6)
        await sleep(milliseconds: 300)

        // (b) timeout: no panel at all -> NO_CHOOSER_OBSERVED (plan §10).
        let timeoutBounds = PostconditionBounds(fastCadenceMs: 60, fastPhaseSeconds: 0.6, slowCadenceMs: 120, hardCapSeconds: 1.0, lateForensicSampleDelaySeconds: 0.4)
        let timeoutSamplerContext = try await makeSamplerContext()
        let timeoutTask = Task.detached {
            await PostconditionMonitor.run(bounds: timeoutBounds) {
                await ChooserAffirmationSampler.sample(context: timeoutSamplerContext)
            }
        }
        let timeoutOutcome = await timeoutTask.value
        switch timeoutOutcome {
        case let .noChooserObserved(count, seconds):
            proof.timeoutOutcome = "noChooserObserved"
            proof.timeoutDetail = "samples=\(count) observed=\(seconds)"
        case let .chooserVerified(affirmation):
            proof.timeoutOutcome = "chooserVerified"
            proof.timeoutDetail = "unexpected affirmation windowID=\(affirmation.windowID)"
        case let .chooserObservedAfterWindow(count, seconds, affirmation):
            proof.timeoutOutcome = "chooserObservedAfterWindow"
            proof.timeoutDetail = "samples=\(count) late=\(seconds) affirmed=\(affirmation != nil)"
        }

        // (c) late-affirmative: panel appears after the hard cap -> CHOOSER_OBSERVED_AFTER_WINDOW.
        let lateBounds = PostconditionBounds(fastCadenceMs: 60, fastPhaseSeconds: 0.6, slowCadenceMs: 120, hardCapSeconds: 1.0, lateForensicSampleDelaySeconds: 0.9)
        let lateSamplerContext = try await makeSamplerContext()
        let lateTask = Task.detached {
            await PostconditionMonitor.run(bounds: lateBounds) {
                await ChooserAffirmationSampler.sample(context: lateSamplerContext)
            }
        }
        await sleep(milliseconds: 300)
        let lateDestination = run.fixturesDir.appendingPathComponent("postcondition-late")
        try EvidenceIO.ensureDirectory(lateDestination)
        _ = try await harnessCall("showPanel", params: ["delayMs": 1400.0, "directory": lateDestination.path, "marker": "late.marker"])
        let latePanelShown = await harness.waitForEvent("panelShown", timeoutSeconds: 4)
        if latePanelShown != nil {
            let diagnostic = await ChooserAffirmationSampler.sample(context: lateSamplerContext)
            proof.lateDiagnosticAffirmed = diagnostic.affirmed != nil
            proof.lateDiagnosticDetail = diagnostic.note ?? "affirmed windowID=\(diagnostic.affirmed?.windowID ?? 0)"
        } else {
            proof.lateDiagnosticDetail = "panelShown event was not observed"
        }
        let lateOutcome = await lateTask.value
        switch lateOutcome {
        case let .chooserObservedAfterWindow(count, seconds, affirmation):
            proof.lateOutcome = "chooserObservedAfterWindow"
            proof.lateAffirmationNonNil = affirmation != nil
            proof.lateDetail = "samples=\(count) lateSeconds=\(seconds) affirmed=\(affirmation != nil)"
        case let .noChooserObserved(count, seconds):
            proof.lateOutcome = "noChooserObserved"
            proof.lateDetail = "samples=\(count) observed=\(seconds)"
        case let .chooserVerified(affirmation):
            proof.lateOutcome = "chooserVerified"
            proof.lateDetail = "unexpected in-window affirmation windowID=\(affirmation.windowID)"
        }
        _ = try? await harnessCall("closePanel")
        _ = await harness.waitForEvent("panelClosed", timeoutSeconds: 6)
        await sleep(milliseconds: 300)

        proof.monitorInputPosts = inputPostCount - postMonitorAt
        proof.zeroFurtherInputDuringMonitors = proof.monitorInputPosts == 0
        proof.atISO8601 = EvidenceIO.iso8601()

        let pass = proof.withinWindowOutcome == "chooserVerified"
            && proof.timeoutOutcome == "noChooserObserved"
            && proof.lateOutcome == "chooserObservedAfterWindow"
            && proof.lateAffirmationNonNil
            && proof.zeroFurtherInputDuringMonitors
        let detail = "within=\(proof.withinWindowOutcome) timeout=\(proof.timeoutOutcome) late=\(proof.lateOutcome)/affirmed=\(proof.lateAffirmationNonNil) monitorPosts=\(proof.monitorInputPosts) maxLatencyMs=\(maxMs) "
        try await recordItem(5, name: "postcondition-bounds-freeze", verdict: pass ? "PASS" : "PARTIAL", detail: detail, fileName: "05-postcondition-bounds.json", value: boundsFreeze)
        try await recordItem(5, name: "postcondition-proofs", verdict: pass ? "PASS" : "PARTIAL", detail: detail, fileName: "05-postcondition-proofs.json", value: proof)
        if pass {
            var revision = 1
            while FileManager.default.fileExists(atPath: run.canonicalFrozenDir.appendingPathComponent("postcondition-bounds-v\(revision).json").path)
                || FileManager.default.fileExists(atPath: run.canonicalFrozenDir.appendingPathComponent("postcondition-latency-observations-v\(revision).json").path) {
                revision += 1
            }
            try recordFrozen("postcondition-bounds-v\(revision).json", value: boundsFreeze)
            try recordFrozen("postcondition-latency-observations-v\(revision).json", value: latencyRecord)
        } else {
            notes.append("NOT_FROZEN: postcondition bounds and latency were not published because the within-window, timeout, or late-affirmative proof was partial")
        }
    }

    // MARK: - Item 7: focus theft

    private func item07FocusTheft() async throws {
        _ = try await occluderCall("hide")
        _ = try await harnessCall("activate")
        _ = try await harnessCall("hidePopup")
        _ = try await harnessCall("setFrame", params: ["x": 160.0, "y": 140.0, "w": 800.0, "h": 600.0])
        await waitForSettle(1.0)
        try await refreshHarnessState()

        guard let ruleBook = frozenRuleBook else {
            try await recordItem(7, name: "focus-theft", verdict: "NOT_RUN", detail: "frozen rule book unavailable", fileName: "07-focus-theft.json", value: ["detail": "no frozen rule book"])
            return
        }
        let identity = try await captureWindowIdentity(ruleBook: ruleBook)
        let dispatches = 0

        let baseline = try await dispatchPrecondition(identity: identity, epoch: identity.captureEpoch)
        let baselineOK = baseline == nil

        let screen = NSScreen.screens.first
        let screenHeight = Double(screen?.frame.height ?? 0)
        let screenWidth = Double(screen?.frame.width ?? 0)
        try await refreshHarnessState()
        if let mainFrame = dictRect(harnessState["mainFrameTopLeft"]) {
            let coverRect = occluderCoverTopLeft(nearMain: mainFrame, screenHeight: screenHeight, screenWidth: screenWidth)
            _ = try await occluderCall("cover", params: ["x": Double(coverRect.origin.x), "y": Double(coverRect.origin.y), "w": Double(coverRect.width), "h": Double(coverRect.height), "activate": true])
        }
        await waitForSettle(0.6)
        let afterTheft = try await dispatchPrecondition(identity: identity, epoch: identity.captureEpoch)
        _ = try await occluderCall("hide")
        _ = try await harnessCall("activate")
        await waitForSettle(0.6)
        let afterRecovery = try await dispatchPrecondition(identity: identity, epoch: identity.captureEpoch)

        _ = try await harnessCall("moveBy", params: ["dx": 55.0, "dy": 35.0])
        await waitForSettle(1.0)
        let afterMove = try await dispatchPrecondition(identity: identity, epoch: identity.captureEpoch)
        let refreshedIdentity = try await captureWindowIdentity(ruleBook: ruleBook)
        let afterRefresh = try await dispatchPrecondition(identity: refreshedIdentity, epoch: refreshedIdentity.captureEpoch)

        let record = FocusTheftRecord(
            focusLostDetected: afterTheft == "focusLost",
            focusLostDetail: "baseline=\(baseline ?? "ok"); afterTheft=\(afterTheft ?? "ok")",
            recoveredAfterReactivation: afterRecovery == nil && baselineOK,
            frameChangeDetected: afterMove == "frameChanged",
            frameChangeDetail: "afterMove=\(afterMove ?? "ok"); afterRefresh=\(afterRefresh ?? "ok")",
            identityRefreshAllowed: afterRefresh == nil,
            dispatchesPostedDuringFixture: dispatches,
            atISO8601: EvidenceIO.iso8601()
        )
        _ = dispatches
        let pass = record.focusLostDetected && record.recoveredAfterReactivation && record.frameChangeDetected && record.identityRefreshAllowed
        let detail = "focusLost=\(record.focusLostDetected) recovered=\(record.recoveredAfterReactivation) frameChanged=\(record.frameChangeDetected) refreshAllowed=\(record.identityRefreshAllowed) dispatches=0"
        try await recordItem(7, name: "focus-theft", verdict: pass ? "PASS" : "PARTIAL", detail: detail, fileName: "07-focus-theft.json", value: record)
    }

    private func dispatchPrecondition(identity: WindowIdentity, epoch: UInt64) async throws -> String? {
        try await refreshHarnessState()
        if !harnessActive() { return "focusLost" }
        if !identity.isValidInEpoch(epoch) { return "epochStale" }
        let content = try await freshContent()
        guard let main = harnessMainWindow(in: content) else { return "windowDisappeared" }
        if main.windowID != identity.windowID { return "identityChanged" }
        let frameDelta = abs(main.frame.minX - identity.windowFrame.minX) + abs(main.frame.minY - identity.windowFrame.minY)
            + abs(main.frame.width - identity.windowFrame.width) + abs(main.frame.height - identity.windowFrame.height)
        if frameDelta > 1.0 { return "frameChanged" }
        return nil
    }

    private func captureWindowIdentity(ruleBook: CaptureGeometryRuleBook) async throws -> WindowIdentity {
        try await refreshHarnessState()
        let content = try await freshContent()
        guard let main = harnessMainWindow(in: content) else {
            throw NSError(domain: "rev28ctl", code: 10, userInfo: [NSLocalizedDescriptionKey: "harness main window not found"])
        }
        let snapshots = harnessSnapshots(in: content).filter { $0.windowID == main.windowID }
        let state = CaptureGeometryState(settled: true, activated: harnessActive(), includeChildWindows: false, ignoreShadows: true)
        let cfg = configuration(includeChild: false, ignoreShadows: true)
        let service = FrameCaptureService(ruleBook: ruleBook)
        let record = try await service.capture(window: main, configuration: cfg, includedWindows: snapshots, state: state, identityTemplate: nil)
        let process = ProcessInstanceID.current(pid: harnessPID()) ?? ProcessInstanceID(pid: harnessPID(), startTimeSeconds: 0, startTimeMicroseconds: 0)
        let axMain = AXDriver.windows(ofApp: harnessPID()).first
        let axRead = AXIdentityRead(
            role: axMain.flatMap { AXDriver.role(of: $0) },
            subrole: axMain.flatMap { AXDriver.subrole(of: $0) },
            title: axMain.flatMap { AXDriver.title(of: $0) }
        )
        let cgEntry = CGWindowEntryRecord(
            windowID: main.windowID,
            frame: main.frame,
            layer: main.windowLayer,
            ownerPID: harnessPID(),
            ownerName: "rev28harness"
        )
        return WindowIdentity(
            bundleID: ProcessIdentity.bundleID(pid: harnessPID()) ?? "com.rev28.harness",
            process: process,
            windowID: main.windowID,
            windowFrame: main.frame,
            ax: axRead,
            cgEntry: cgEntry,
            captureEpoch: record.epoch,
            captureImageSHA256: record.imageSHA256
        )
    }

    // MARK: - Item 8: tripwire attribution

    private func item08TripwireAttribution() async throws {
        let root = URL(fileURLWithPath: "/tmp/rev28-harness-\(run.runID)")
        let stagingRunDir = root.appendingPathComponent("staging-run")
        let outsideDir = URL(fileURLWithPath: "/tmp/rev28-outside-\(run.runID)")
        try EvidenceIO.ensureDirectory(stagingRunDir)
        try EvidenceIO.ensureDirectory(root)
        try EvidenceIO.ensureDirectory(outsideDir)
        let scope = TripwireScope(stagingRunDir: stagingRunDir, approvedRoot: root)
        let harnessPIDValue = harnessPID()
        let occluderPIDValue = occluder.process.processIdentifier
        var classifications: [TripwireClassification] = []

        // L1 attributable -> expected staging evidence.
        _ = try await harnessCall("writeFiles", params: ["directory": stagingRunDir.appendingPathComponent("photos").path, "mode": "normal", "count": 2])
        classifications.append(TripwireClassifier.classify(
            event: TripwireEvent(path: stagingRunDir.appendingPathComponent("photos/photo-000.jpg"), phase: .postDispatch, attributableToThisRun: true, writerPID: harnessPIDValue, notes: "harness download simulation inside the staging run dir"),
            scope: scope
        ))

        // L2 attributable -> attributed external write (non-fatal, disclosed).
        _ = try await harnessCall("writeFiles", params: ["directory": root.appendingPathComponent("attributable-writes").path, "mode": "normal", "count": 1])
        classifications.append(TripwireClassifier.classify(
            event: TripwireEvent(path: root.appendingPathComponent("attributable-writes/photo-000.jpg"), phase: .postDispatch, attributableToThisRun: true, writerPID: harnessPIDValue, notes: "harness write inside the approved root"),
            scope: scope
        ))

        // L2 unattributable -> fail closed.
        _ = try await occluderCall("writeFile", params: ["path": root.appendingPathComponent("unattributed/x.bin").path, "bytes": 64])
        classifications.append(TripwireClassifier.classify(
            event: TripwireEvent(path: root.appendingPathComponent("unattributed/x.bin"), phase: .postDispatch, attributableToThisRun: false, writerPID: occluderPIDValue, notes: "unrelated writer process inside the approved root"),
            scope: scope
        ))

        // L3 unattributable -> non-aborting environmental context.
        _ = try await occluderCall("writeFile", params: ["path": outsideDir.appendingPathComponent("y.bin").path, "bytes": 64])
        classifications.append(TripwireClassifier.classify(
            event: TripwireEvent(path: outsideDir.appendingPathComponent("y.bin"), phase: .postDispatch, attributableToThisRun: false, writerPID: occluderPIDValue, notes: "unrelated writer process outside the approved root"),
            scope: scope
        ))

        // L3 attributable -> scope violation.
        _ = try await harnessCall("writeFiles", params: ["directory": outsideDir.appendingPathComponent("attributable").path, "mode": "normal", "count": 1])
        classifications.append(TripwireClassifier.classify(
            event: TripwireEvent(path: outsideDir.appendingPathComponent("attributable/photo-000.jpg"), phase: .postDispatch, attributableToThisRun: true, writerPID: harnessPIDValue, notes: "harness write outside the approved root"),
            scope: scope
        ))

        // Accepted-baseline modification flag (classification only; no baseline write).
        let baselineClassification = TripwireClassifier.classify(
            event: TripwireEvent(path: root.appendingPathComponent("synthetic-accepted-baseline-fixture"), phase: .postDispatch, attributableToThisRun: false, modifiesAcceptedBaseline: true, writerPID: nil, notes: "synthetic flag only: the real accepted baseline was never written by the harness fixture"),
            scope: scope
        )
        classifications.append(baselineClassification)

        // Pre-dispatch activity is context.
        classifications.append(TripwireClassifier.classify(
            event: TripwireEvent(path: outsideDir.appendingPathComponent("pre-dispatch.bin"), phase: .preDispatch, attributableToThisRun: false, writerPID: occluderPIDValue, notes: "pre-dispatch environmental activity"),
            scope: scope
        ))

        let expectedOutcomes: [(TripwireLevel, TripwireAttributionOutcome, Bool)] = [
            (.l1StagingRunDir, .stagingExpectedEvidence, false),
            (.l2ApprovedRoot, .attributedExternalWriteObserved, false),
            (.l2ApprovedRoot, .abortedUnattributedFilesystemWrite, true),
            (.l3OutsideApprovedRoot, .environmentalContext, false),
            (.l3OutsideApprovedRoot, .abortedWriteOutsideApprovedRoot, true),
            (.l2ApprovedRoot, .abortedBaselineModified, true),
            (.l3OutsideApprovedRoot, .preDispatchContext, false),
        ]
        let allMatch = zip(classifications, expectedOutcomes).allSatisfy { pair in
            pair.0.level == pair.1.0 && pair.0.outcome == pair.1.1 && pair.0.aborts == pair.1.2
        }
        let record = TripwireRecord(
            fixtureRoot: root.path,
            stagingRunDir: stagingRunDir.path,
            approvedRoot: root.path,
            outsideDir: outsideDir.path,
            harnessPID: harnessPIDValue,
            occluderPID: occluderPIDValue,
            classifications: classifications,
            allExpectedOutcomesMatched: allMatch,
            baselinePathEvent: baselineClassification,
            baselineUntouchedNote: "modifiesAcceptedBaseline=true is a synthetic classification flag on a fixture path; no accepted-baseline path was read or written",
            atISO8601: EvidenceIO.iso8601()
        )
        let detail = classifications.map { "\($0.level.rawValue):\($0.outcome.rawValue)" }.joined(separator: ",")
        try await recordItem(8, name: "tripwire-attribution", verdict: allMatch ? "PASS" : "PARTIAL", detail: detail, fileName: "08-tripwire-attribution.json", value: record)
        try recordFrozen("tripwire-attribution-ladder-v1.json", value: record)
    }

    // MARK: - Item 9: restart/observe-only fixture

    private func item09RestartFixture() async throws {
        let ledgerDir = run.fixturesDir.appendingPathComponent("ledger")
        try EvidenceIO.ensureDirectory(ledgerDir)
        let points = ["afterIntentFsync", "afterDispatch", "midPostcondition", "midDownload"]
        var records: [RestartPointRecord] = []

        for point in points {
            let ledgerURL = ledgerDir.appendingPathComponent("ledger-\(point).jsonl")
            let headURL = ledgerDir.appendingPathComponent("head-\(point).json")
            let child = Process()
            child.executableURL = options.binaryDirectory.appendingPathComponent("rev28ctl")
            child.arguments = ["restart-child", "--ledger", ledgerURL.path, "--head-file", headURL.path, "--point", point]
            child.standardOutput = FileHandle.nullDevice
            child.standardError = FileHandle.nullDevice
            let startedAt = Date()
            try child.run()
            child.waitUntilExit()
            let observedSeconds = Date().timeIntervalSince(startedAt)
            let sawSIGKILL = child.terminationReason == .uncaughtSignal && child.terminationStatus == SIGKILL

            var childHead: String?
            var childSeq: Int?
            if let headData = try? Data(contentsOf: headURL),
               let headObject = try? JSONSerialization.jsonObject(with: headData) as? [String: Any] {
                childHead = headObject["headHash"] as? String
                childSeq = (headObject["seq"] as? NSNumber)?.intValue
            }

            var chainVerified = false
            var entriesAfterReload = 0
            var headMatches = false
            var resumeMode = "unavailable"
            var dispatchCount = -1
            var allowedNew = -1
            var wouldRefuse = false
            if FileManager.default.fileExists(atPath: ledgerURL.path) {
                let ledger = try IntentLedger(fileURL: ledgerURL)
                entriesAfterReload = ledger.entries.count
                do {
                    try IntentLedger.verify(entries: ledger.entries)
                    chainVerified = true
                } catch {
                    chainVerified = false
                }
                headMatches = childHead != nil && ledger.headHash == childHead
                let decision = LedgerResume.decide(entries: ledger.entries)
                resumeMode = decision.mode
                dispatchCount = decision.irreversibleDispatchCount
                allowedNew = decision.allowedNewIrreversibleDispatches
                wouldRefuse = LedgerResume.wouldRefuseNewIrreversibleDispatch(entries: ledger.entries)
            }
            records.append(RestartPointRecord(
                point: point,
                childPID: child.processIdentifier,
                terminationStatus: child.terminationStatus,
                terminationReason: child.terminationReason == .uncaughtSignal ? "uncaughtSignal" : "exit",
                sawSIGKILL: sawSIGKILL,
                entriesAfterReload: entriesAfterReload,
                chainVerified: chainVerified,
                headMatchesChildHeadFile: headMatches,
                headHash: childHead,
                childHeadHash: childHead,
                resumeMode: resumeMode,
                irreversibleDispatchCount: dispatchCount,
                allowedNewIrreversibleDispatches: allowedNew,
                wouldRefuseNewIrreversibleDispatch: wouldRefuse,
                observedSeconds: observedSeconds
            ))
            _ = childSeq
        }

        // Control: a fresh reviewed decision recorded after the last irreversible
        // dispatch arms exactly one new irreversible dispatch.
        let controlURL = ledgerDir.appendingPathComponent("ledger-freshReviewed-control.jsonl")
        let controlLedger = try IntentLedger(fileURL: controlURL)
        _ = try controlLedger.append(kind: "intent.saved", payload: ["fixture": "control"])
        _ = try controlLedger.append(kind: "dispatch.saveAll", payload: ["fixture": "control"])
        _ = try controlLedger.append(kind: "decision.freshReviewed", payload: ["armIrreversible": "1"])
        let controlDecision = LedgerResume.decide(entries: controlLedger.entries)

        let record = RestartFixtureRecord(
            ledgerDir: ledgerDir.path,
            points: records,
            allPointsObserveOnly: records.allSatisfy { $0.resumeMode == "observeOnly" },
            allChainsContinuous: records.allSatisfy { $0.chainVerified && $0.headMatchesChildHeadFile },
            zeroNewIrreversibleDispatches: records.allSatisfy { $0.allowedNewIrreversibleDispatches == 0 && $0.wouldRefuseNewIrreversibleDispatch },
            freshReviewedControl: "allowedNewIrreversibleDispatches=\(controlDecision.allowedNewIrreversibleDispatches) reason=\(controlDecision.reason)",
            atISO8601: EvidenceIO.iso8601()
        )
        let allExpected = records.allSatisfy { $0.sawSIGKILL && $0.chainVerified && $0.headMatchesChildHeadFile }
        let pass = allExpected && record.allPointsObserveOnly && record.zeroNewIrreversibleDispatches && controlDecision.allowedNewIrreversibleDispatches == 1
        let detail = "points=\(records.count) sigkill=\(records.filter { $0.sawSIGKILL }.count) chainVerified=\(records.filter { $0.chainVerified }.count) observeOnly=\(records.filter { $0.resumeMode == "observeOnly" }.count) zeroNewIrreversible=\(record.zeroNewIrreversibleDispatches) controlAllowed=\(controlDecision.allowedNewIrreversibleDispatches)"
        try await recordItem(9, name: "restart-observe-only", verdict: pass ? "PASS" : "PARTIAL", detail: detail, fileName: "09-restart-observe-only.json", value: record)
        try recordFrozen("restart-observe-only-fixture-v1.json", value: record)
    }
}
