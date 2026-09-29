import AppKit
import ApplicationServices
import CoreGraphics
import Foundation
import Rev28Core
import ScreenCaptureKit

// MARK: - Current-composer calibration (plan TEST_STRATEGY item 6 / TEST_ORDER step 5; V-02)
//
// Append-only recalibration of the frozen Rev28 rules against the *current*
// native composer: the real NSOpenPanel presented by the bundled rev28harness
// synthetic app, sampled by the real strict postcondition monitor through
// SCK + CG + AX, with a separate-process occluder and a real input sink.
//
// Contract:
//  * the canonical frozen directory is READ-ONLY input; every frozen artifact
//    used is bound by SHA-256 into the run record and is never rewritten;
//  * no LINE process is launched, observed, addressed or dispatched into;
//    every target is the harness bundle (com.openai.rev28.harness) or the
//    occluder sibling process;
//  * keyboard input is posted only after the harness bundle is provably the
//    frontmost application and its panel is the key window;
//  * every record is written atomically into a fresh append-only run directory.

struct ComposerCalibrationOptions {
    let evidenceBase: URL
    let binaryDirectory: URL
    let frozenDirectory: URL
    let timingCount: Int
    let diagnoseOnly: Bool
}

struct ComposerFrozenBinding: Codable {
    let name: String
    let sha256: String
    let bytes: Int
}

struct ComposerCapabilityRecord: Codable {
    let probeBinarySHA256: String
    let probeRecordPath: String
    let probeRecordSHA256: String
    let overallStatus: String?
    let axIsProcessTrusted: Bool?
    let cgPreflightScreenCaptureAccess: Bool?
    let cgPreflightPostEventAccess: Bool?
    let screenCaptureKitStatus: String?
    let visionStatus: String?
    let quartzKeyboardConstructionOK: Bool?
    let hostOSVersion: String?
    let hostOSBuild: String?
    let atISO8601: String
}

struct ComposerSessionRecord: Codable {
    let screenLocked: Bool
    let onConsole: Bool?
    let loginDone: Bool?
    let consoleUser: String?
    let frontmostBundleID: String?
    let frontmostIsLoginWindow: Bool
    let atISO8601: String
}

struct ComposerGeometryCellRecord: Codable {
    let settled: Bool
    let activated: Bool
    let includeChildWindows: Bool
    let ignoreShadows: Bool
    let stateKey: String
    let frozenRulePresent: Bool
    let validity: String
    let violations: [String]
    let imageWidthPx: Int
    let imageHeightPx: Int
    let scale: Double
    let perSideSizeDeltaPt: [String: Double]
    let expectedBBoxPt: [Double]
    let actualBBoxPt: [Double]
    let markerFound: Bool
    let markerPixel: [Int]?
    let predictedMarkerPixel: [Int]?
    let markerPixelDeltaXPx: Double?
    let markerPixelDeltaYPx: Double?
    let contentOriginLocalPt: [Double]
    let contentOriginReportedPt: [Double]
    let screenHeightPt: Double
    let measuredMarkerOffsetXPt: Double?
    let measuredMarkerOffsetYPt: Double?
    let withinFrozenTolerance: Bool
    let imageSHA256: String
    let capturedAtISO8601: String
}

struct ComposerGeometryRecord: Codable {
    let ruleBookID: String
    let ruleBookSHA256: String
    let windowFrameTopLeftPt: [Double]
    let cells: [ComposerGeometryCellRecord]
    let allCellsValid: Bool
    let allMarkersWithinTolerance: Bool
    let atISO8601: String
}

struct ComposerChooserCalibrationRecord: Codable {
    let panelWindowFound: Bool
    let panelLocatedVia: String
    let axCandidateWindows: [String]
    let sckHarnessWindowIDs: [UInt32]
    let matchedSCKWindowID: UInt32?
    let observedWindowRole: String?
    let observedWindowSubrole: String?
    let observedWindowTitle: String?
    let observedWindowFramePt: [Double]
    let observedButtonTitles: [String]
    let observedRoles: [String]
    let observedSubroles: [String]
    let observedTextFieldRoles: [String]
    let observedPopUpRoles: [String]
    let frozenCalibrationSHA256: String
    let frozenButtonTitles: [String]
    let frozenWindowRole: String?
    let frozenWindowSubrole: String?
    let defaultButtonTitlesObserved: [String]
    let cancelButtonTitlesObserved: [String]
    let matchesFrozenCalibration: Bool
    let frozenPredicateID: String
    let derivedPredicateID: String?
    let derivedPredicateClauses: String?
    let predicateDerivationError: String?
    let mismatches: [String]
    let atISO8601: String
}

struct ComposerMonitorTimingSample: Codable {
    let index: Int
    let outcome: String
    let affirmed: Bool
    let windowID: UInt32?
    let framePt: [Double]?
    let sampleCount: Int
    let dispatchToAffirmedMs: Double?
    let willShowToAffirmedMs: Double?
    let willShowToShownMs: Double?
    let willShowAtUnix: Double?
    let shownAtUnix: Double?
    let monitorElapsedSeconds: Double?
    let frozenPredicateAffirmed: Bool?
    let derivedPredicateAffirmed: Bool?
    let samplerNote: String?
    let samplerHistogram: [String: Int]?
}

struct ComposerMonitorTimingsRecord: Codable {
    let boundsUsed: [String: Double]
    let plannedCount: Int
    let completedCount: Int
    let allAffirmedInWindow: Bool
    let withinWindowMaxMs: Double
    let withinWindowMedianMs: Double
    let withinWindowP95Ms: Double
    let withinWindowWillShowMaxMs: Double
    let frozenBoundsSHA256: String
    let frozenRecordedMaxMs: Double
    let frozenRecordedMedianMs: Double
    let frozenFastPhaseSeconds: Double
    let frozenHardCapSeconds: Double
    let maxAffirmedBelowFastPhase: Bool
    let inputPostsDuringMonitors: Int
    let samples: [ComposerMonitorTimingSample]
    let timeoutCase: ComposerMonitorTimingSample?
    let delayedCase: ComposerMonitorTimingSample?
    let lateCase: ComposerMonitorTimingSample?
    let atISO8601: String
}

struct ComposerDestinationRecord: Codable {
    let destinationPath: String
    let startingDirectoryPath: String
    let affirmationObserved: Bool
    let affirmationWindowID: UInt32?
    let harnessFrontmostAtInput: Bool
    let frontmostBundleIDAtInput: String?
    let navigationCandidates: [String]
    let destinationReflectedAfterNavigation: Bool
    let confirmationAction: String?
    let axPressDispatchCount: Int
    let keyboardPostsForConfirmation: Int
    let panelClosedEventObserved: Bool
    let markerFileName: String
    let markerWrittenAtDestination: Bool
    let panelSelectedURL: String?
    let panelSelectedMatchesDestination: Bool
    let atISO8601: String
}

struct ComposerRefusalCaseRecord: Codable {
    let caseID: String
    let scenario: String
    let expected: String
    let observedOutcome: String
    let observedDetail: String
    let affirmed: Bool
    let irreversibleDispatches: Int
    let inputPosts: Int
    let passed: Bool
}

struct ComposerRefusalMatrixRecord: Codable {
    let cases: [ComposerRefusalCaseRecord]
    let allPassed: Bool
    let atISO8601: String
}

struct ComposerApplicabilityVerdict: Codable {
    let taskID: String
    let frozenBindings: [ComposerFrozenBinding]
    let geometryRecheckPass: Bool
    let chooserCalibrationPass: Bool
    let strictMonitorTimingsPass: Bool
    let destinationConfirmationPass: Bool
    let refusalMatrixPass: Bool
    let harnessBundleIDObserved: String?
    let harnessPID: Int32?
    let realLineInteraction: String
    let overallVerdict: String
    let blocker: String?
    let atISO8601: String
}

struct ComposerRunSummary: Codable {
    let runRoot: String
    let taskID: String
    let startedAtISO8601: String
    let durationSeconds: Double
    let timingCount: Int
    let geometryPass: Bool
    let chooserPass: Bool
    let timingsPass: Bool
    let destinationPass: Bool
    let refusalsPass: Bool
    let overallVerdict: String
    let blocker: String?
    let notes: [String]
    let inputPostsTotal: Int
    let axPressTotal: Int
}

private struct ComposerSamplerContext: Sendable {
    let harnessPID: Int32
    let preWindowIDs: Set<UInt32>
    let preCensus: [Int32]
    let preOwner: ChooserProcessFacts
    let frozenPredicate: ChooserAffirmationPredicate
    let derivedPredicate: ChooserAffirmationPredicate?
}

private struct ComposerSamplerEntry: Sendable {
    let note: String
    let windowID: UInt32?
    let framePt: [Double]?
    let frozenAffirmed: Bool
    let derivedAffirmed: Bool?
    let axNodeCount: Int?
    let sampledAtUnix: Double
}

private actor ComposerSamplerTelemetry {
    private var entries: [ComposerSamplerEntry] = []

    func append(_ entry: ComposerSamplerEntry) {
        entries.append(entry)
    }

    func drain() -> [ComposerSamplerEntry] {
        let out = entries
        entries = []
        return out
    }
}

/// Strict-monitor sampler over the *current* composer. Cheap negative sampling:
/// the synchronous CG inventory is only a candidate-presence gate; a positive
/// result still requires fresh SCK + CG + AX evidence and the full frozen
/// chooser predicate before it can affirm.
private enum ComposerChooserSampler {
    static func sample(
        context: ComposerSamplerContext,
        telemetry: ComposerSamplerTelemetry
    ) async -> PostconditionSample {
        let cgInventory = CGWindowInventory.onScreenWindows()
        let newCGCandidateIDs = Set(cgInventory.compactMap { window -> UInt32? in
            guard window.ownerPID == context.harnessPID,
                  !context.preWindowIDs.contains(window.windowNumber) else { return nil }
            return window.windowNumber
        })
        guard !newCGCandidateIDs.isEmpty else {
            await telemetry.append(ComposerSamplerEntry(
                note: "noNewCGChooserCandidate",
                windowID: nil,
                framePt: nil,
                frozenAffirmed: false,
                derivedAffirmed: nil,
                axNodeCount: nil,
                sampledAtUnix: Date().timeIntervalSince1970
            ))
            return PostconditionSample(affirmed: nil, note: "noNewCGChooserCandidate")
        }

        do {
            let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
            let postCensus = Array(Set(content.windows.compactMap { $0.owningApplication?.processID })).sorted()
            let candidates = content.windows.filter { window in
                window.owningApplication?.processID == context.harnessPID
                    && window.isOnScreen
                    && newCGCandidateIDs.contains(window.windowID)
            }
            guard !candidates.isEmpty else {
                let note = "newCGCandidatePendingFreshSCK ids=\(newCGCandidateIDs.sorted())"
                await telemetry.append(ComposerSamplerEntry(
                    note: note,
                    windowID: nil,
                    framePt: nil,
                    frozenAffirmed: false,
                    derivedAffirmed: nil,
                    axNodeCount: nil,
                    sampledAtUnix: Date().timeIntervalSince1970
                ))
                return PostconditionSample(affirmed: nil, note: note)
            }

            var rejectionDetails: [String] = []
            for window in candidates {
                guard let axElement = matchingAXWindow(pid: context.harnessPID, frame: window.frame) else {
                    rejectionDetails.append("windowID=\(window.windowID) cause=axWindowNotYetMatched")
                    continue
                }
                let dump = AXDriver.dump(element: axElement, pid: context.harnessPID, maxDepth: 8, maxNodes: 500)
                let postOwner = ProcessIdentity.reading(pid: context.harnessPID)
                let candidate = ChooserCandidate(
                    windowID: window.windowID,
                    frame: window.frame,
                    onScreen: true,
                    presentInSCInventory: true,
                    presentInCGInventory: cgInventory.contains { $0.windowNumber == window.windowID },
                    isNewRelativeToPreDispatchInventory: !context.preWindowIDs.contains(window.windowID),
                    owner: postOwner,
                    pidReuseDetected: false,
                    axNodes: dump.nodes,
                    preDispatchCensusPIDs: context.preCensus,
                    postDispatchCensusPIDs: postCensus,
                    preDispatchOwner: context.preOwner,
                    postDispatchOwner: postOwner
                )
                let frozenVerdict = ChooserAffirmationEvaluator.evaluate(candidate: candidate, predicate: context.frozenPredicate)
                let derivedVerdict = context.derivedPredicate.map {
                    ChooserAffirmationEvaluator.evaluate(candidate: candidate, predicate: $0)
                }
                let derivedAffirmed: Bool?
                switch derivedVerdict {
                case .none: derivedAffirmed = nil
                case let .some(.affirmed): derivedAffirmed = true
                case .some(.refused): derivedAffirmed = false
                }
                switch frozenVerdict {
                case .affirmed:
                    await telemetry.append(ComposerSamplerEntry(
                        note: "affirmed",
                        windowID: window.windowID,
                        framePt: [window.frame.minX, window.frame.minY, window.frame.width, window.frame.height],
                        frozenAffirmed: true,
                        derivedAffirmed: derivedAffirmed,
                        axNodeCount: dump.nodes.count,
                        sampledAtUnix: Date().timeIntervalSince1970
                    ))
                    return PostconditionSample(affirmed: ChooserAffirmation(
                        windowID: window.windowID,
                        frame: window.frame,
                        ownerPID: context.harnessPID,
                        predicateID: context.frozenPredicate.predicateID,
                        affirmedAtISO8601: EvidenceIO.iso8601()
                    ))
                case let .refused(cause, detail):
                    rejectionDetails.append("windowID=\(window.windowID) cause=\(cause.rawValue) \(detail)")
                    await telemetry.append(ComposerSamplerEntry(
                        note: "refused \(cause.rawValue): \(detail)",
                        windowID: window.windowID,
                        framePt: [window.frame.minX, window.frame.minY, window.frame.width, window.frame.height],
                        frozenAffirmed: false,
                        derivedAffirmed: derivedAffirmed,
                        axNodeCount: dump.nodes.count,
                        sampledAtUnix: Date().timeIntervalSince1970
                    ))
                }
            }
            let note = rejectionDetails.isEmpty ? "noEligibleChooserCandidate" : rejectionDetails.joined(separator: "; ")
            await telemetry.append(ComposerSamplerEntry(
                note: note,
                windowID: nil,
                framePt: nil,
                frozenAffirmed: false,
                derivedAffirmed: nil,
                axNodeCount: nil,
                sampledAtUnix: Date().timeIntervalSince1970
            ))
            return PostconditionSample(affirmed: nil, note: note)
        } catch {
            let note = "samplerError:\(error)"
            await telemetry.append(ComposerSamplerEntry(
                note: note,
                windowID: nil,
                framePt: nil,
                frozenAffirmed: false,
                derivedAffirmed: nil,
                axNodeCount: nil,
                sampledAtUnix: Date().timeIntervalSince1970
            ))
            return PostconditionSample(affirmed: nil, note: note)
        }
    }

    static func matchingAXWindow(pid: Int32, frame: CGRect) -> AXUIElement? {
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

/// Invokes the strict monitor with the `monotonicNow`/`sleep` closures passed
/// *explicitly*. Swift 6.3 (Xcode 27 / macOS 27 beta) miscompiles
/// default-argument async closures across module boundaries: the library and
/// client copies of a default-argument async closure disagree on the async
/// context size, so the default `sleep` closure overflows its context and
/// corrupts the task allocator (swiftlang/swift#92017; the observable symptom is
/// `freed pointer was not the last allocation` from `swift_task_dealloc`, i.e. a
/// SIGABRT inside the monitor). Passing the closures from this module keeps a
/// single copy in the link and avoids the mismatch entirely. The defaults on
/// `PostconditionMonitor.run` remain for the frozen W2 CI path and are never
/// exercised by this driver.
private func runCurrentComposerMonitor(
    bounds: PostconditionBounds,
    sampler: @escaping @Sendable () async -> PostconditionSample
) async -> PostconditionOutcome {
    await PostconditionMonitor.run(
        bounds: bounds,
        sampler: sampler,
        monotonicNow: { Double(DispatchTime.now().uptimeNanoseconds) / 1_000_000_000.0 },
        sleep: { seconds in
            try? await Task.sleep(nanoseconds: UInt64(max(0.001, seconds) * 1_000_000_000))
        }
    )
}

// MARK: - Driver

@MainActor
final class ComposerCalibrationDriver {
    private let options: ComposerCalibrationOptions
    private let runRoot: URL
    private let itemsDir: URL
    private let logsDir: URL
    private let fixturesDir: URL
    private let bundleExecutable: URL
    private var harness: ProcessPeer?
    private var occluder: ProcessPeer?
    private var harnessPID: Int32 = 0
    private var harnessState: [String: Any] = [:]
    private var frozenBindings: [ComposerFrozenBinding] = []
    private var frozenRuleBook: CaptureGeometryRuleBook?
    private var frozenPredicate: ChooserAffirmationPredicate?
    private var frozenButtonTitles: [String] = []
    private var derivedPredicate: ChooserAffirmationPredicate?
    private var predicateDerivationError: String?
    private var inputPostCount = 0
    private var axPressCount = 0
    private var notes: [String] = []
    private let harnessBundleID = "com.openai.rev28.harness"
    private let taskID = "T20260925-0647-01-rev28-native-closed-loop"
    private let atStart = Date()

    init(options: ComposerCalibrationOptions) throws {
        self.options = options
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyyMMdd-HHmmss"
        formatter.timeZone = TimeZone.current
        let stamp = formatter.string(from: Date())
        self.runRoot = options.evidenceBase.appendingPathComponent("COMPOSER-\(stamp)")
        self.itemsDir = runRoot.appendingPathComponent("items")
        self.logsDir = runRoot.appendingPathComponent("logs")
        self.fixturesDir = runRoot.appendingPathComponent("fixtures")
        self.bundleExecutable = runRoot
            .appendingPathComponent("bundle/Rev28Harness.app/Contents/MacOS/rev28harness")
        for directory in [runRoot, itemsDir, logsDir, fixturesDir] {
            try EvidenceIO.ensureDirectory(directory)
        }
    }

    // MARK: helpers

    private func sleep(milliseconds: Double) async {
        try? await Task.sleep(nanoseconds: UInt64(max(0, milliseconds) * 1_000_000))
    }

    private func writeItem<T: Encodable>(_ name: String, _ value: T) throws -> (path: String, sha: String) {
        let url = itemsDir.appendingPathComponent(name)
        let sha = try EvidenceIO.writeJSONAtomically(value, to: url)
        return (url.path, sha)
    }

    private func bindFrozen(_ name: String) throws {
        let url = options.frozenDirectory.appendingPathComponent(name)
        let data = try Data(contentsOf: url)
        frozenBindings.append(ComposerFrozenBinding(
            name: name,
            sha256: EvidenceIO.sha256Hex(data),
            bytes: data.count
        ))
    }

    @discardableResult
    private func harnessCall(_ command: String, params: [String: Any] = [:], timeoutSeconds: Double = 20) async throws -> [String: Any] {
        guard let harness else { throw NSError(domain: "composer-calibration", code: 1, userInfo: [NSLocalizedDescriptionKey: "harness is not running"]) }
        let reply = try await harness.send(command, params: params, timeoutSeconds: timeoutSeconds)
        if (reply["ok"] as? Bool) == false {
            throw NSError(domain: "composer-calibration", code: 2, userInfo: [NSLocalizedDescriptionKey: "harness refused \(command): \(reply["error"] ?? "?")"])
        }
        if command == "state" || reply["pid"] != nil {
            harnessState = reply
        }
        return reply
    }

    @discardableResult
    private func occluderCall(_ command: String, params: [String: Any] = [:]) async throws -> [String: Any] {
        guard let occluder else { throw NSError(domain: "composer-calibration", code: 3, userInfo: [NSLocalizedDescriptionKey: "occluder is not running"]) }
        return try await occluder.send(command, params: params, timeoutSeconds: 20)
    }

    @discardableResult
    private func refreshState() async throws -> [String: Any] {
        try await harnessCall("state")
    }

    private func harnessWindowIDs() async throws -> Set<UInt32> {
        let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
        return Set(content.windows.compactMap { $0.owningApplication?.processID == harnessPID ? $0.windowID : nil })
    }

    private func topLeftFrame(from state: [String: Any]) -> CGRect? {
        guard let frame = state["mainFrameTopLeft"] as? [String: Double],
              let x = frame["x"], let y = frame["y"], let w = frame["w"], let h = frame["h"] else { return nil }
        return CGRect(x: x, y: y, width: w, height: h)
    }

    private func ensureHarnessFrontmostWithKeyPanel(timeoutSeconds: Double = 4.0) async -> Bool {
        let deadline = Date().addingTimeInterval(timeoutSeconds)
        while Date() < deadline {
            let front = NSWorkspace.shared.frontmostApplication?.bundleIdentifier
            let state = (try? await refreshState()) ?? [:]
            let panelKey = (state["panelKeyWindow"] as? Bool) ?? false
            let active = (state["active"] as? Bool) ?? false
            if front == harnessBundleID, panelKey, active { return true }
            await sleep(milliseconds: 100)
        }
        return false
    }

    // MARK: session state
    //
    // Every item in this calibration depends on a live, unlocked console
    // session: a locked screen refuses NSApp activation, keeps panels off the
    // window server's on-screen list and blocks key-window/input dispatch. A
    // locked session is therefore a hard precondition, not a partial verdict.

    private func currentSessionRecord() -> ComposerSessionRecord {
        let dict = (CGSessionCopyCurrentDictionary() as? [String: Any]) ?? [:]
        let locked = ((dict["CGSSessionScreenIsLocked"] as? NSNumber)?.boolValue) ?? false
        let frontmost = NSWorkspace.shared.frontmostApplication
        return ComposerSessionRecord(
            screenLocked: locked,
            onConsole: (dict["kCGSSessionOnConsoleKey"] as? NSNumber)?.boolValue,
            loginDone: (dict["kCGSessionLoginDoneKey"] as? NSNumber)?.boolValue,
            consoleUser: dict["kCGSSessionUserNameKey"] as? String,
            frontmostBundleID: frontmost?.bundleIdentifier,
            frontmostIsLoginWindow: frontmost?.bundleIdentifier == "com.apple.loginwindow",
            atISO8601: EvidenceIO.iso8601()
        )
    }

    private func waitForHarnessActivation(timeoutSeconds: Double) async -> Bool {
        let deadline = Date().addingTimeInterval(timeoutSeconds)
        while Date() < deadline {
            let state = (try? await refreshState()) ?? [:]
            let active = (state["active"] as? Bool) ?? false
            let front = NSWorkspace.shared.frontmostApplication?.bundleIdentifier
            if active, front == harnessBundleID { return true }
            await sleep(milliseconds: 150)
        }
        return false
    }

    // Balanced panel event discipline: drain stale events before a dispatch,
    // consume the willShow/shown pair, and consume panelClosed after a close.
    // Without the pre-dispatch drain a stale panelWillShow from an earlier item
    // is returned for the next dispatch and pollutes timing measurements.
    private func drainHarnessEvents() {
        _ = harness?.drainEvents()
    }

    private func showPanelBalanced(
        directory: String,
        marker: String,
        expectedDirectory: String? = nil,
        delayMs: Double = 0.0,
        eventTimeoutSeconds: Double = 8.0
    ) async throws -> (willShow: [String: Any]?, shown: [String: Any]?) {
        drainHarnessEvents()
        var params: [String: Any] = ["delayMs": delayMs, "directory": directory, "marker": marker]
        if let expectedDirectory { params["expectedDirectory"] = expectedDirectory }
        _ = try await harnessCall("showPanel", params: params)
        let willShow = await harness?.waitForEvent("panelWillShow", timeoutSeconds: eventTimeoutSeconds)
        let shown = await harness?.waitForEvent("panelShown", timeoutSeconds: eventTimeoutSeconds)
        return (willShow, shown)
    }

    @discardableResult
    private func closePanelBalanced(timeoutSeconds: Double = 8.0) async -> [String: Any]? {
        _ = try? await harnessCall("closePanel")
        let closed = await harness?.waitForEvent("panelClosed", timeoutSeconds: timeoutSeconds)
        drainHarnessEvents()
        return closed
    }

    // MARK: prepare

    private func prepareEnvironment() async throws {
        // 1. Read-only binding of every frozen artifact this run depends on.
        for name in [
            "capture-geometry-rulebook-v1.json",
            "chooser-affirmation-predicate-v2.json",
            "chooser-ax-calibration-v2.json",
            "postcondition-bounds-v3.json",
            "postcondition-latency-observations-v3.json",
            "tripwire-attribution-ladder-v1.json",
        ] {
            try bindFrozen(name)
        }
        let ruleBookData = try Data(contentsOf: options.frozenDirectory.appendingPathComponent("capture-geometry-rulebook-v1.json"))
        frozenRuleBook = try JSONDecoder().decode(CaptureGeometryRuleBook.self, from: ruleBookData)
        let predicateData = try Data(contentsOf: options.frozenDirectory.appendingPathComponent("chooser-affirmation-predicate-v2.json"))
        frozenPredicate = try JSONDecoder().decode(ChooserAffirmationPredicate.self, from: predicateData)
        let calibrationData = try Data(contentsOf: options.frozenDirectory.appendingPathComponent("chooser-ax-calibration-v2.json"))
        if let object = try JSONSerialization.jsonObject(with: calibrationData) as? [String: Any],
           let titles = object["buttonTitles"] as? [String] {
            frozenButtonTitles = titles
        }

        // 2. Bundle the harness so the synthetic composer has a real bundle id.
        let contents = bundleExecutable.deletingLastPathComponent().deletingLastPathComponent()
        let sourceBinary = options.binaryDirectory.appendingPathComponent("rev28harness")
        try EvidenceIO.ensureDirectory(bundleExecutable.deletingLastPathComponent())
        if FileManager.default.fileExists(atPath: bundleExecutable.path) {
            try FileManager.default.removeItem(at: bundleExecutable)
        }
        try FileManager.default.copyItem(at: sourceBinary, to: bundleExecutable)
        try FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: bundleExecutable.path)
        let plist = """
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
          <key>CFBundleIdentifier</key><string>\(harnessBundleID)</string>
          <key>CFBundleName</key><string>Rev28Harness</string>
          <key>CFBundleExecutable</key><string>rev28harness</string>
          <key>CFBundlePackageType</key><string>APPL</string>
          <key>CFBundleVersion</key><string>1</string>
          <key>CFBundleShortVersionString</key><string>1.0</string>
          <key>NSHighResolutionCapable</key><true/>
        </dict>
        </plist>
        """
        try Data(plist.utf8).write(to: contents.appendingPathComponent("Info.plist"), options: .atomic)

        // 3. Capability probe in this exact process context (V-01 refresh).
        try await runCapabilityProbe()

        // 4. Separate-process occluder.
        let occluderProcess = try ProcessPeer(
            executableURL: options.binaryDirectory.appendingPathComponent("rev28occluder"),
            arguments: [],
            name: "rev28occluder",
            logURL: logsDir.appendingPathComponent("rev28occluder-stdout.log")
        )
        occluder = occluderProcess

        // 5. Harness bundle.
        let harnessProcess = try ProcessPeer(
            executableURL: bundleExecutable,
            arguments: [],
            name: "rev28harness",
            logURL: logsDir.appendingPathComponent("rev28harness-stdout.log")
        )
        harness = harnessProcess
        guard let ready = await harnessProcess.waitForEvent("ready", timeoutSeconds: 15),
              let pidNumber = ready["pid"] as? NSNumber else {
            throw NSError(domain: "composer-calibration", code: 4, userInfo: [NSLocalizedDescriptionKey: "harness did not emit ready"])
        }
        harnessPID = pidNumber.int32Value
        try await refreshState()
    }

    private func runCapabilityProbe() async throws {
        let probeURL = options.binaryDirectory.appendingPathComponent("rev28probe")
        let probeOut = runRoot.appendingPathComponent("capability-probe")
        try EvidenceIO.ensureDirectory(probeOut)
        let process = Process()
        process.executableURL = probeURL
        process.arguments = [probeOut.path]
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe
        try process.run()
        _ = pipe.fileHandleForReading.readDataToEndOfFile()
        process.waitUntilExit()

        let records = try FileManager.default.contentsOfDirectory(at: probeOut, includingPropertiesForKeys: nil)
            .filter { $0.pathExtension == "json" }
            .sorted { $0.lastPathComponent < $1.lastPathComponent }
        guard let recordURL = records.last else {
            throw NSError(domain: "composer-calibration", code: 5, userInfo: [NSLocalizedDescriptionKey: "capability probe produced no record"])
        }
        let recordData = try Data(contentsOf: recordURL)
        let object = (try? JSONSerialization.jsonObject(with: recordData)) as? [String: Any] ?? [:]
        let trust = object["trust"] as? [String: Any] ?? [:]
        let sck = object["screenCaptureKit"] as? [String: Any] ?? [:]
        let vision = object["vision"] as? [String: Any] ?? [:]
        let quartz = object["quartz"] as? [String: Any] ?? [:]
        let probeBinaryData = try Data(contentsOf: probeURL)
        let record = ComposerCapabilityRecord(
            probeBinarySHA256: EvidenceIO.sha256Hex(probeBinaryData),
            probeRecordPath: recordURL.path,
            probeRecordSHA256: EvidenceIO.sha256Hex(recordData),
            overallStatus: object["overallStatus"] as? String,
            axIsProcessTrusted: trust["axIsProcessTrusted"] as? Bool,
            cgPreflightScreenCaptureAccess: trust["cgPreflightScreenCaptureAccess"] as? Bool,
            cgPreflightPostEventAccess: trust["cgPreflightPostEventAccess"] as? Bool,
            screenCaptureKitStatus: sck["status"] as? String,
            visionStatus: vision["status"] as? String,
            quartzKeyboardConstructionOK: quartz["keyboardEventConstructionOK"] as? Bool,
            hostOSVersion: object["hostOSVersion"] as? String,
            hostOSBuild: object["hostOSBuild"] as? String,
            atISO8601: EvidenceIO.iso8601()
        )
        _ = try writeItem("00-capability-probe.json", record)
        if record.overallStatus != "PASS" || record.axIsProcessTrusted != true || record.cgPreflightScreenCaptureAccess != true {
            notes.append("CAPABILITY_PARTIAL: probe status=\(record.overallStatus ?? "?") ax=\(record.axIsProcessTrusted.map(String.init) ?? "?") screen=\(record.cgPreflightScreenCaptureAccess.map(String.init) ?? "?")")
        }
    }

    // MARK: item 2 — capture geometry recheck against the frozen rule book

    private func redMarkerTopLeftPixel(in image: CGImage) -> (x: Int, y: Int)? {
        let width = image.width
        let height = image.height
        var buffer = [UInt8](repeating: 0, count: width * height * 4)
        let ok = buffer.withUnsafeMutableBytes { raw -> Bool in
            guard let context = CGContext(
                data: raw.baseAddress,
                width: width,
                height: height,
                bitsPerComponent: 8,
                bytesPerRow: width * 4,
                space: CGColorSpaceCreateDeviceRGB(),
                bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
            ) else { return false }
            context.interpolationQuality = .none
            context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
            return true
        }
        guard ok else { return nil }
        for y in 0..<height {
            for x in 0..<width {
                let index = (y * width + x) * 4
                let red = Int(buffer[index])
                let green = Int(buffer[index + 1])
                let blue = Int(buffer[index + 2])
                if red > 200, green < 90, blue < 90 {
                    return (x, y)
                }
            }
        }
        return nil
    }

    private func itemGeometryRecheck() async throws {
        _ = try await occluderCall("hide")
        _ = try await harnessCall("activate")
        _ = try await harnessCall("hidePopup")
        _ = try await harnessCall("setFrame", params: ["x": 160.0, "y": 140.0, "w": 800.0, "h": 600.0])
        await sleep(milliseconds: 800)
        let state = try await refreshState()
        guard let mainFrame = topLeftFrame(from: state),
              let contentOriginDict = state["contentOriginLocalTopLeft"] as? [String: Double],
              let contentOriginX = contentOriginDict["x"], let contentOriginY = contentOriginDict["y"],
              let screenHeight = (state["screenHeight"] as? NSNumber)?.doubleValue else {
            throw NSError(domain: "composer-calibration", code: 6, userInfo: [NSLocalizedDescriptionKey: "harness state lacks main window geometry"])
        }
        // The harness reports `contentOriginLocalTopLeft` with x in screen-global
        // points (contentRect.minX) and y as the top inset measured against the
        // bottom-left frame; normalize both to window-local top-left points so
        // the red marker drawn at content (4,4) can be predicted in captured
        // pixels through the recorded transform (invariant 4).
        let contentOriginLocalX = contentOriginX - mainFrame.minX
        let frameBottomInset = screenHeight - mainFrame.minY - mainFrame.height
        let contentOriginLocalY = contentOriginY + frameBottomInset
        let markerWindowLocal = WindowLocalPoint(x: contentOriginLocalX + 4.0, y: contentOriginLocalY + 4.0)
        let content = try await WindowSensor.shareableContent()
        let snapshots = WindowSensor.snapshots(from: content)
        guard let mainSnapshot = snapshots.first(where: { snapshot in
            snapshot.ownerPID == harnessPID
                && abs(snapshot.frame.minX - mainFrame.minX) <= 6
                && abs(snapshot.frame.minY - mainFrame.minY) <= 6
                && abs(snapshot.frame.width - mainFrame.width) <= 6
        }), let scWindow = content.windows.first(where: { $0.windowID == mainSnapshot.windowID }) else {
            throw NSError(domain: "composer-calibration", code: 7, userInfo: [NSLocalizedDescriptionKey: "harness main window not found in SCK inventory"])
        }
        let children = WindowSensor.childWindows(of: mainSnapshot, in: snapshots)
        let service = FrameCaptureService(ruleBook: frozenRuleBook, initialEpoch: 0)

        var cells: [ComposerGeometryCellRecord] = []
        let combos: [(settled: Bool, includeChild: Bool)] = [(true, false), (false, false), (true, true)]
        for combo in combos {
            if combo.settled {
                await sleep(milliseconds: 600)
            } else {
                _ = try await harnessCall("moveBy", params: ["dx": 0.0, "dy": 12.0])
                _ = try await harnessCall("moveBy", params: ["dx": 0.0, "dy": -12.0])
            }
            let activatedNow = (try await refreshState())["active"] as? Bool ?? false
            let geometryState = CaptureGeometryState(
                settled: combo.settled,
                activated: activatedNow,
                includeChildWindows: combo.includeChild,
                ignoreShadows: true
            )
            let configuration = combo.includeChild ? CaptureConfiguration.childUnion : CaptureConfiguration.primaryWindow
            let included = combo.includeChild ? ([mainSnapshot] + children) : [mainSnapshot]
            let (record, image) = try await service.captureWithImage(
                window: scWindow,
                configuration: configuration,
                includedWindows: included,
                state: geometryState,
                identityTemplate: nil
            )
            let rule = frozenRuleBook?.rule(for: geometryState)
            let marker = redMarkerTopLeftPixel(in: image)
            let geometry = CaptureGeometry(
                windowFrame: mainFrame,
                captureBBox: record.actualBBoxPt,
                scale: record.scale
            )
            let predictedPixel = geometry.capturePixelPoint(fromScreen: geometry.screenPoint(fromWindowLocal: markerWindowLocal))
            let predictedMarkerPixel = [Int(predictedPixel.x.rounded()), Int(predictedPixel.y.rounded())]
            var offsetX: Double?
            var offsetY: Double?
            var markerDeltaXPx: Double?
            var markerDeltaYPx: Double?
            if let marker {
                let measuredLocal = geometry.windowLocalPoint(fromCapturePixel: CapturePixelPoint(x: Double(marker.x), y: Double(marker.y)))
                offsetX = measuredLocal.x - markerWindowLocal.x
                offsetY = measuredLocal.y - markerWindowLocal.y
                markerDeltaXPx = Double(marker.x) - predictedPixel.x
                markerDeltaYPx = Double(marker.y) - predictedPixel.y
            }
            let tolerance = rule?.maxOriginPaddingPt ?? 1.0
            let markerWithin = marker != nil
                && abs(offsetX ?? .infinity) <= tolerance
                && abs(offsetY ?? .infinity) <= tolerance
            cells.append(ComposerGeometryCellRecord(
                settled: combo.settled,
                activated: activatedNow,
                includeChildWindows: combo.includeChild,
                ignoreShadows: true,
                stateKey: record.stateKey,
                frozenRulePresent: rule != nil,
                validity: record.validity.rawValue,
                violations: record.violations,
                imageWidthPx: record.imageWidthPx,
                imageHeightPx: record.imageHeightPx,
                scale: record.scale,
                perSideSizeDeltaPt: [
                    "top": record.perSideSizeDeltaPt.top,
                    "left": record.perSideSizeDeltaPt.left,
                    "bottom": record.perSideSizeDeltaPt.bottom,
                    "right": record.perSideSizeDeltaPt.right,
                ],
                expectedBBoxPt: [record.expectedBBoxPt.minX, record.expectedBBoxPt.minY, record.expectedBBoxPt.width, record.expectedBBoxPt.height],
                actualBBoxPt: [record.actualBBoxPt.minX, record.actualBBoxPt.minY, record.actualBBoxPt.width, record.actualBBoxPt.height],
                markerFound: marker != nil,
                markerPixel: marker.map { [$0.x, $0.y] },
                predictedMarkerPixel: marker != nil ? predictedMarkerPixel : nil,
                markerPixelDeltaXPx: markerDeltaXPx,
                markerPixelDeltaYPx: markerDeltaYPx,
                contentOriginLocalPt: [contentOriginLocalX, contentOriginLocalY],
                contentOriginReportedPt: [contentOriginX, contentOriginY],
                screenHeightPt: screenHeight,
                measuredMarkerOffsetXPt: offsetX,
                measuredMarkerOffsetYPt: offsetY,
                withinFrozenTolerance: record.validity == .valid && markerWithin,
                imageSHA256: record.imageSHA256,
                capturedAtISO8601: record.capturedAtISO8601
            ))
        }

        let ruleBookSHA = frozenBindings.first { $0.name == "capture-geometry-rulebook-v1.json" }?.sha256 ?? ""
        let record = ComposerGeometryRecord(
            ruleBookID: frozenRuleBook?.ruleID ?? "?",
            ruleBookSHA256: ruleBookSHA,
            windowFrameTopLeftPt: [mainFrame.minX, mainFrame.minY, mainFrame.width, mainFrame.height],
            cells: cells,
            allCellsValid: cells.allSatisfy { $0.validity == FrameValidity.valid.rawValue },
            allMarkersWithinTolerance: cells.allSatisfy { $0.withinFrozenTolerance },
            atISO8601: EvidenceIO.iso8601()
        )
        _ = try writeItem("02-geometry-recheck.json", record)
    }

    // MARK: item 3 — chooser AX calibration against the frozen predicate

    private func frameDistancePt(_ a: CGRect, _ b: CGRect) -> Double {
        Double(abs(a.minX - b.minX) + abs(a.minY - b.minY) + abs(a.width - b.width) + abs(a.height - b.height))
    }

    /// Locates the real NSOpenPanel by scanning the harness AX tree with a
    /// bounded retry. SCK is deliberately not the locator here: a freshly
    /// created panel can lag the shareable-content inventory, while the AX
    /// window tree is authoritative for existence (the frozen calibration
    /// located the panel the same way, with an empty SCK inventory).
    private func locateChooserAXWindow(
        pid: Int32,
        timeoutSeconds: Double
    ) async -> (element: AXUIElement, title: String?, frame: CGRect, via: String, candidates: [String])? {
        let deadline = Date().addingTimeInterval(timeoutSeconds)
        while true {
            var candidates: [String] = []
            var titledMatch: (AXUIElement, String?, CGRect)?
            var structuralMatch: (AXUIElement, String?, CGRect)?
            for window in AXDriver.windows(ofApp: pid) {
                let role = AXDriver.role(of: window) ?? "nil"
                let subrole = AXDriver.subrole(of: window) ?? "nil"
                let title = AXDriver.title(of: window)
                let frame = AXDriver.frame(of: window)
                let frameText = frame.map {
                    "[x=\(Int($0.minX.rounded())) y=\(Int($0.minY.rounded())) w=\(Int($0.width.rounded())) h=\(Int($0.height.rounded()))]"
                } ?? "nil"
                candidates.append("title=\(title ?? "nil") role=\(role) subrole=\(subrole) frame=\(frameText)")
                guard let frame else { continue }
                if titledMatch == nil, title == "rev28 harness chooser" {
                    titledMatch = (window, title, frame)
                }
                if structuralMatch == nil {
                    let hasTextField = AXDriver.firstDescendant(of: window, maxDepth: 8) { candidate in
                        AXDriver.role(of: candidate) == "AXTextField"
                    } != nil
                    let hasButton = AXDriver.firstDescendant(of: window, maxDepth: 8) { candidate in
                        AXDriver.role(of: candidate) == "AXButton"
                    } != nil
                    if hasTextField && hasButton { structuralMatch = (window, title, frame) }
                }
            }
            if let match = titledMatch { return (match.0, match.1, match.2, "axTitle", candidates) }
            if let match = structuralMatch { return (match.0, match.1, match.2, "axTextAndButton", candidates) }
            if Date() >= deadline { return nil }
            await sleep(milliseconds: 150)
        }
    }

    private func itemChooserCalibration() async throws {
        _ = try await occluderCall("hide")
        let start = fixturesDir.appendingPathComponent("chooser-calibration-start")
        try EvidenceIO.ensureDirectory(start)
        _ = try await harnessCall("activate")
        let shown = try await showPanelBalanced(
            directory: start.path,
            marker: "chooser-calibration.marker"
        ).shown
        var calibrationRecord: ComposerChooserCalibrationRecord?
        if shown != nil {
            let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
            let sckHarnessWindows = content.windows.filter { window in
                window.owningApplication?.processID == harnessPID && window.isOnScreen
            }
            var observed: ChooserAXCalibrationEvidence?
            var observedFrame = CGRect.zero
            var observedTitle: String?
            var locatedVia = "notLocated"
            var axCandidates: [String] = []
            var matchedSCKWindowID: UInt32?
            if let located = await locateChooserAXWindow(pid: harnessPID, timeoutSeconds: 4.0) {
                observedTitle = located.title
                observedFrame = located.frame
                locatedVia = located.via
                axCandidates = located.candidates
                matchedSCKWindowID = sckHarnessWindows.first { frameDistancePt($0.frame, located.frame) <= 6 }?.windowID
                let dump = AXDriver.dump(element: located.element, pid: harnessPID, maxDepth: 8, maxNodes: 500)
                var roles: Set<String> = []
                var subroles: Set<String> = []
                var textFieldRoles: Set<String> = []
                var popUpRoles: Set<String> = []
                var buttonTitles: [String] = []
                for node in dump.nodes {
                    if let role = node.role { roles.insert(role) }
                    if let subrole = node.subrole { subroles.insert(subrole) }
                    if node.role == "AXTextField" { textFieldRoles.insert("AXTextField") }
                    if node.role == "AXPopUpButton" { popUpRoles.insert("AXPopUpButton") }
                    if node.role == "AXButton" { buttonTitles.append(node.title ?? "?") }
                }
                observed = ChooserAXCalibrationEvidence(
                    panelWindowFound: true,
                    panelWindowRole: AXDriver.role(of: located.element),
                    panelWindowSubrole: AXDriver.subrole(of: located.element),
                    buttonTitles: buttonTitles,
                    rolesObserved: roles.sorted(),
                    subrolesObserved: subroles.sorted(),
                    textFieldRoles: textFieldRoles.sorted(),
                    popUpRoles: popUpRoles.sorted()
                )
            }

            if let observed, let frozenPredicate {
                var mismatches: [String] = []
                let frozenCalibrationObject = (try? JSONSerialization.jsonObject(
                    with: Data(contentsOf: options.frozenDirectory.appendingPathComponent("chooser-ax-calibration-v2.json"))
                )) as? [String: Any]
                if let frozenRoles = frozenCalibrationObject?["rolesObserved"] as? [String] {
                    for role in ["AXButton", "AXTextField", "AXPopUpButton"] where !(observed.rolesObserved.contains(role)) || !frozenRoles.contains(role) {
                        mismatches.append("role \(role) not observed in both current and frozen calibration")
                    }
                }
                for role in frozenPredicate.ax.textFieldRoles where !observed.textFieldRoles.contains(role) {
                    mismatches.append("frozen text-field role \(role) not observed")
                }
                for role in frozenPredicate.ax.popUpButtonRoles where !observed.popUpRoles.contains(role) {
                    mismatches.append("frozen pop-up role \(role) not observed")
                }
                if observed.panelWindowRole != frozenPredicate.ax.windowRole {
                    mismatches.append("window role \(observed.panelWindowRole ?? "nil") != frozen \(frozenPredicate.ax.windowRole)")
                }
                if let subrole = observed.panelWindowSubrole, !frozenPredicate.ax.allowedSubroles.contains(subrole) {
                    mismatches.append("window subrole \(subrole) not in frozen allowed subroles")
                }
                let observedTitles = Set(observed.buttonTitles)
                let defaultObserved = ["開啟", "Open", "打開"].filter(observedTitles.contains)
                let cancelObserved = ["Cancel", "取消"].filter(observedTitles.contains)
                if defaultObserved.isEmpty { mismatches.append("no frozen default-button title observed") }
                if cancelObserved.isEmpty { mismatches.append("no frozen cancel-button title observed") }

                do {
                    let derived = try ChooserProductionPredicate.derive(
                        frozen: frozenPredicate,
                        calibration: observed,
                        defaultButtonTitles: defaultObserved,
                        cancelButtonTitles: cancelObserved
                    )
                    derivedPredicate = derived
                    predicateDerivationError = nil
                } catch {
                    predicateDerivationError = String(describing: error)
                    mismatches.append("predicate derivation failed: \(error)")
                }

                calibrationRecord = ComposerChooserCalibrationRecord(
                    panelWindowFound: true,
                    panelLocatedVia: locatedVia,
                    axCandidateWindows: axCandidates,
                    sckHarnessWindowIDs: sckHarnessWindows.map { $0.windowID },
                    matchedSCKWindowID: matchedSCKWindowID,
                    observedWindowRole: observed.panelWindowRole,
                    observedWindowSubrole: observed.panelWindowSubrole,
                    observedWindowTitle: observedTitle,
                    observedWindowFramePt: [observedFrame.minX, observedFrame.minY, observedFrame.width, observedFrame.height],
                    observedButtonTitles: observed.buttonTitles,
                    observedRoles: observed.rolesObserved,
                    observedSubroles: observed.subrolesObserved,
                    observedTextFieldRoles: observed.textFieldRoles,
                    observedPopUpRoles: observed.popUpRoles,
                    frozenCalibrationSHA256: frozenBindings.first { $0.name == "chooser-ax-calibration-v2.json" }?.sha256 ?? "",
                    frozenButtonTitles: frozenButtonTitles,
                    frozenWindowRole: frozenPredicate.ax.windowRole,
                    frozenWindowSubrole: frozenPredicate.ax.allowedSubroles.first,
                    defaultButtonTitlesObserved: defaultObserved,
                    cancelButtonTitlesObserved: cancelObserved,
                    matchesFrozenCalibration: mismatches.isEmpty,
                    frozenPredicateID: frozenPredicate.predicateID,
                    derivedPredicateID: derivedPredicate?.predicateID,
                    derivedPredicateClauses: derivedPredicate.map { "version=\($0.predicateVersion) default=\($0.ax.defaultButton.map { $0.titles.joined(separator: ",") } ?? "nil") cancel=\($0.ax.cancelButton.map { $0.titles.joined(separator: ",") } ?? "nil")" },
                    predicateDerivationError: predicateDerivationError,
                    mismatches: mismatches,
                    atISO8601: EvidenceIO.iso8601()
                )
            } else {
                calibrationRecord = ComposerChooserCalibrationRecord(
                    panelWindowFound: false,
                    panelLocatedVia: locatedVia,
                    axCandidateWindows: axCandidates,
                    sckHarnessWindowIDs: sckHarnessWindows.map { $0.windowID },
                    matchedSCKWindowID: matchedSCKWindowID,
                    observedWindowRole: nil,
                    observedWindowSubrole: nil,
                    observedWindowTitle: observedTitle,
                    observedWindowFramePt: [],
                    observedButtonTitles: [],
                    observedRoles: [],
                    observedSubroles: [],
                    observedTextFieldRoles: [],
                    observedPopUpRoles: [],
                    frozenCalibrationSHA256: frozenBindings.first { $0.name == "chooser-ax-calibration-v2.json" }?.sha256 ?? "",
                    frozenButtonTitles: frozenButtonTitles,
                    frozenWindowRole: frozenPredicate?.ax.windowRole,
                    frozenWindowSubrole: nil,
                    defaultButtonTitlesObserved: [],
                    cancelButtonTitlesObserved: [],
                    matchesFrozenCalibration: false,
                    frozenPredicateID: frozenPredicate?.predicateID ?? "?",
                    derivedPredicateID: nil,
                    derivedPredicateClauses: nil,
                    predicateDerivationError: "panel window not located",
                    mismatches: ["panel window not located in AX tree"],
                    atISO8601: EvidenceIO.iso8601()
                )
            }
        }
        _ = await closePanelBalanced()
        await sleep(milliseconds: 250)
        if let calibrationRecord {
            _ = try writeItem("03-chooser-ax-calibration.json", calibrationRecord)
        }
    }

    // MARK: item 4 — >=20 panel timings under the strict monitor

    private func parseISO8601(_ text: String) -> Date? {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = formatter.date(from: text) { return date }
        let fallback = ISO8601DateFormatter()
        fallback.formatOptions = [.withInternetDateTime]
        return fallback.date(from: text)
    }

    private func makeSamplerContext() async throws -> ComposerSamplerContext {
        let preWindowIDs = try await harnessWindowIDs()
        let preCensus = Array(Set(CGWindowInventory.onScreenWindows().map { $0.ownerPID })).sorted()
        let preOwner = ProcessIdentity.reading(pid: harnessPID)
        guard let frozenPredicate else {
            throw NSError(domain: "composer-calibration", code: 8, userInfo: [NSLocalizedDescriptionKey: "frozen predicate not loaded"])
        }
        return ComposerSamplerContext(
            harnessPID: harnessPID,
            preWindowIDs: preWindowIDs,
            preCensus: preCensus,
            preOwner: preOwner,
            frozenPredicate: frozenPredicate,
            derivedPredicate: derivedPredicate
        )
    }

    private func outcomeDescription(_ outcome: PostconditionOutcome) -> (name: String, affirmed: ChooserAffirmation?, sampleCount: Int, elapsed: Double?) {
        switch outcome {
        case let .chooserVerified(affirmation):
            return ("chooserVerified", affirmation, 0, nil)
        case let .noChooserObserved(sampleCount, observedSeconds):
            return ("noChooserObserved", nil, sampleCount, observedSeconds)
        case let .chooserObservedAfterWindow(sampleCount, lateSampleSeconds, affirmation):
            return ("chooserObservedAfterWindow", affirmation, sampleCount, lateSampleSeconds)
        }
    }

    private func itemStrictMonitorTimings() async throws {
        let postsAtStart = inputPostCount
        _ = try await occluderCall("hide")
        _ = try await harnessCall("activate")
        _ = try await harnessCall("hidePopup")
        _ = try await harnessCall("setFrame", params: ["x": 160.0, "y": 140.0, "w": 800.0, "h": 600.0])
        await sleep(milliseconds: 600)

        var samples: [ComposerMonitorTimingSample] = []
        let telemetry = ComposerSamplerTelemetry()
        for index in 1...options.timingCount {
            let destination = fixturesDir.appendingPathComponent("timings/destination-\(index)")
            try EvidenceIO.ensureDirectory(destination)
            let context = try await makeSamplerContext()
            _ = await telemetry.drain()
            let postsBefore = inputPostCount
            let monitorTask = Task.detached {
                let outcome = await runCurrentComposerMonitor(bounds: PostconditionBounds.planTime) {
                    await ComposerChooserSampler.sample(context: context, telemetry: telemetry)
                }
                return outcome
            }
            await sleep(milliseconds: 100)
            let dispatchAt = Date()
            let events = try await showPanelBalanced(
                directory: destination.path,
                marker: "timing-\(index).marker",
                eventTimeoutSeconds: 10
            )
            let willShow = events.willShow
            let shown = events.shown
            let willShowAt = (willShow?["at"] as? NSNumber)?.doubleValue
            let shownAt = (shown?["at"] as? NSNumber)?.doubleValue
            let outcome = await monitorTask.value
            let description = outcomeDescription(outcome)
            let entries = await telemetry.drain()
            let entry = entries.last
            let histogram = entries.isEmpty ? nil : entries.reduce(into: [String: Int]()) { $0[$1.note, default: 0] += 1 }
            var dispatchToAffirmed: Double?
            var willShowToAffirmed: Double?
            if let affirmation = description.affirmed, let affirmedAt = parseISO8601(affirmation.affirmedAtISO8601) {
                dispatchToAffirmed = affirmedAt.timeIntervalSince(dispatchAt) * 1000.0
                if let willShowAt {
                    willShowToAffirmed = (affirmedAt.timeIntervalSince1970 - willShowAt) * 1000.0
                }
            }
            let willShowToShown: Double? = {
                guard let willShowAt, let shownAt else { return nil }
                return (shownAt - willShowAt) * 1000.0
            }()
            samples.append(ComposerMonitorTimingSample(
                index: index,
                outcome: description.name,
                affirmed: description.affirmed != nil,
                windowID: description.affirmed?.windowID,
                framePt: description.affirmed.map { [$0.frame.minX, $0.frame.minY, $0.frame.width, $0.frame.height] },
                sampleCount: description.sampleCount,
                dispatchToAffirmedMs: dispatchToAffirmed,
                willShowToAffirmedMs: willShowToAffirmed,
                willShowToShownMs: willShowToShown,
                willShowAtUnix: willShowAt,
                shownAtUnix: shownAt,
                monitorElapsedSeconds: description.elapsed,
                frozenPredicateAffirmed: entry?.frozenAffirmed,
                derivedPredicateAffirmed: entry?.derivedAffirmed,
                samplerNote: entry?.note,
                samplerHistogram: histogram
            ))
            if inputPostCount != postsBefore {
                notes.append("INPUT_POSTED_DURING_MONITOR index=\(index)")
            }
            _ = await closePanelBalanced()
            await sleep(milliseconds: 200)
        }

        // Timeout case: no panel at all inside a short bounded window.
        let timeoutBounds = PostconditionBounds(
            fastCadenceMs: 60,
            fastPhaseSeconds: 0.6,
            slowCadenceMs: 120,
            hardCapSeconds: 1.0,
            lateForensicSampleDelaySeconds: 0.9
        )
        let timeoutContext = try await makeSamplerContext()
        let timeoutOutcome = await runCurrentComposerMonitor(bounds: timeoutBounds) {
            await ComposerChooserSampler.sample(context: timeoutContext, telemetry: telemetry)
        }
        let timeoutDescription = outcomeDescription(timeoutOutcome)
        let timeoutEntry = (await telemetry.drain()).last
        let timeoutCase = ComposerMonitorTimingSample(
            index: 0,
            outcome: timeoutDescription.name,
            affirmed: timeoutDescription.affirmed != nil,
            windowID: timeoutDescription.affirmed?.windowID,
            framePt: nil,
            sampleCount: timeoutDescription.sampleCount,
            dispatchToAffirmedMs: nil,
            willShowToAffirmedMs: nil,
            willShowToShownMs: nil,
            willShowAtUnix: nil,
            shownAtUnix: nil,
            monitorElapsedSeconds: timeoutDescription.elapsed,
            frozenPredicateAffirmed: timeoutEntry?.frozenAffirmed,
            derivedPredicateAffirmed: timeoutEntry?.derivedAffirmed,
            samplerNote: timeoutEntry?.note ?? "noPanelDispatched",
            samplerHistogram: nil
        )

        // Delayed panel: scheduled appearance strictly inside the fast phase.
        let delayedDestination = fixturesDir.appendingPathComponent("timings/destination-delayed")
        try EvidenceIO.ensureDirectory(delayedDestination)
        let delayedContext = try await makeSamplerContext()
        let delayedTask = Task.detached {
            await runCurrentComposerMonitor(bounds: PostconditionBounds.planTime) {
                await ComposerChooserSampler.sample(context: delayedContext, telemetry: telemetry)
            }
        }
        await sleep(milliseconds: 100)
        let delayedDispatchAt = Date()
        let delayedEvents = try await showPanelBalanced(
            directory: delayedDestination.path,
            marker: "timing-delayed.marker",
            delayMs: 900.0,
            eventTimeoutSeconds: 10
        )
        let delayedWillShow = delayedEvents.willShow
        let delayedShown = delayedEvents.shown
        let delayedOutcome = await delayedTask.value
        let delayedDescription = outcomeDescription(delayedOutcome)
        let delayedEntry = (await telemetry.drain()).last
        var delayedDispatchToAffirmed: Double?
        if let affirmation = delayedDescription.affirmed, let affirmedAt = parseISO8601(affirmation.affirmedAtISO8601) {
            delayedDispatchToAffirmed = affirmedAt.timeIntervalSince(delayedDispatchAt) * 1000.0
        }
        let delayedCase = ComposerMonitorTimingSample(
            index: 0,
            outcome: delayedDescription.name,
            affirmed: delayedDescription.affirmed != nil,
            windowID: delayedDescription.affirmed?.windowID,
            framePt: delayedDescription.affirmed.map { [$0.frame.minX, $0.frame.minY, $0.frame.width, $0.frame.height] },
            sampleCount: delayedDescription.sampleCount,
            dispatchToAffirmedMs: delayedDispatchToAffirmed,
            willShowToAffirmedMs: nil,
            willShowToShownMs: nil,
            willShowAtUnix: (delayedWillShow?["at"] as? NSNumber)?.doubleValue,
            shownAtUnix: (delayedShown?["at"] as? NSNumber)?.doubleValue,
            monitorElapsedSeconds: delayedDescription.elapsed,
            frozenPredicateAffirmed: delayedEntry?.frozenAffirmed,
            derivedPredicateAffirmed: delayedEntry?.derivedAffirmed,
            samplerNote: "panelWillShowObserved=\(delayedWillShow != nil)",
            samplerHistogram: nil
        )
        _ = await closePanelBalanced()
        await sleep(milliseconds: 200)

        // Late case: appearance strictly after the hard cap but before the
        // single forensic sample -> CHOOSER_OBSERVED_AFTER_WINDOW, never promoted.
        let lateContext = try await makeSamplerContext()
        let lateTask = Task.detached {
            await runCurrentComposerMonitor(bounds: timeoutBounds) {
                await ComposerChooserSampler.sample(context: lateContext, telemetry: telemetry)
            }
        }
        await sleep(milliseconds: 100)
        let lateDestination = fixturesDir.appendingPathComponent("timings/destination-late")
        try EvidenceIO.ensureDirectory(lateDestination)
        let lateEvents = try await showPanelBalanced(
            directory: lateDestination.path,
            marker: "timing-late.marker",
            delayMs: 1150.0,
            eventTimeoutSeconds: 6
        )
        let lateOutcome = await lateTask.value
        let lateDescription = outcomeDescription(lateOutcome)
        let lateEntry = (await telemetry.drain()).last
        let lateCase = ComposerMonitorTimingSample(
            index: 0,
            outcome: lateDescription.name,
            affirmed: lateDescription.affirmed != nil,
            windowID: lateDescription.affirmed?.windowID,
            framePt: lateDescription.affirmed.map { [$0.frame.minX, $0.frame.minY, $0.frame.width, $0.frame.height] },
            sampleCount: lateDescription.sampleCount,
            dispatchToAffirmedMs: nil,
            willShowToAffirmedMs: nil,
            willShowToShownMs: nil,
            willShowAtUnix: (lateEvents.willShow?["at"] as? NSNumber)?.doubleValue,
            shownAtUnix: (lateEvents.shown?["at"] as? NSNumber)?.doubleValue,
            monitorElapsedSeconds: lateDescription.elapsed,
            frozenPredicateAffirmed: lateEntry?.frozenAffirmed,
            derivedPredicateAffirmed: lateEntry?.derivedAffirmed,
            samplerNote: lateEntry?.note,
            samplerHistogram: nil
        )
        _ = await closePanelBalanced()
        await sleep(milliseconds: 300)

        func percentile(_ values: [Double], _ fraction: Double) -> Double {
            guard !values.isEmpty else { return 0 }
            let sorted = values.sorted()
            let index = Int((Double(sorted.count - 1) * fraction).rounded(.up))
            return sorted[min(max(index, 0), sorted.count - 1)]
        }
        let affirmedLatencies = samples.compactMap { $0.dispatchToAffirmedMs }
        let willShowLatencies = samples.compactMap { $0.willShowToShownMs }
        let boundsObject = try JSONSerialization.jsonObject(
            with: Data(contentsOf: options.frozenDirectory.appendingPathComponent("postcondition-bounds-v3.json"))
        ) as? [String: Any] ?? [:]
        let frozenBounds = boundsObject["frozenBounds"] as? [String: Any] ?? [:]
        let frozenEvidence = try JSONSerialization.jsonObject(
            with: Data(contentsOf: options.frozenDirectory.appendingPathComponent("postcondition-latency-observations-v3.json"))
        ) as? [String: Any] ?? [:]
        let fastPhase = (frozenBounds["fastPhaseSeconds"] as? NSNumber)?.doubleValue ?? 8
        let record = ComposerMonitorTimingsRecord(
            boundsUsed: [
                "fastCadenceMs": Double(PostconditionBounds.planTime.fastCadenceMs),
                "fastPhaseSeconds": PostconditionBounds.planTime.fastPhaseSeconds,
                "slowCadenceMs": Double(PostconditionBounds.planTime.slowCadenceMs),
                "hardCapSeconds": PostconditionBounds.planTime.hardCapSeconds,
                "lateForensicSampleDelaySeconds": PostconditionBounds.planTime.lateForensicSampleDelaySeconds,
            ],
            plannedCount: options.timingCount,
            completedCount: samples.count,
            allAffirmedInWindow: samples.count == options.timingCount && samples.allSatisfy { $0.outcome == "chooserVerified" },
            withinWindowMaxMs: affirmedLatencies.max() ?? 0,
            withinWindowMedianMs: percentile(affirmedLatencies, 0.5),
            withinWindowP95Ms: percentile(affirmedLatencies, 0.95),
            withinWindowWillShowMaxMs: willShowLatencies.max() ?? 0,
            frozenBoundsSHA256: frozenBindings.first { $0.name == "postcondition-bounds-v3.json" }?.sha256 ?? "",
            frozenRecordedMaxMs: (frozenEvidence["maxObservedMs"] as? NSNumber)?.doubleValue ?? 0,
            frozenRecordedMedianMs: (frozenEvidence["medianObservedMs"] as? NSNumber)?.doubleValue ?? 0,
            frozenFastPhaseSeconds: fastPhase,
            frozenHardCapSeconds: (frozenBounds["hardCapSeconds"] as? NSNumber)?.doubleValue ?? 15,
            maxAffirmedBelowFastPhase: (affirmedLatencies.max() ?? .infinity) < fastPhase * 1000.0,
            inputPostsDuringMonitors: inputPostCount - postsAtStart,
            samples: samples,
            timeoutCase: timeoutCase,
            delayedCase: delayedCase,
            lateCase: lateCase,
            atISO8601: EvidenceIO.iso8601()
        )
        _ = try writeItem("04-strict-monitor-timings.json", record)
    }

    // MARK: item 5 — destination preparation + exactly one AXPress

    private func itemDestinationConfirmation() async throws -> ComposerDestinationRecord {
        _ = try await occluderCall("hide")
        let start = fixturesDir.appendingPathComponent("destination-start")
        let destination = fixturesDir.appendingPathComponent("destination-ok")
        try EvidenceIO.ensureDirectory(start)
        try EvidenceIO.ensureDirectory(destination)
        let markerName = "composer-calibration.marker"
        let markerURL = destination.appendingPathComponent(markerName)
        if FileManager.default.fileExists(atPath: markerURL.path) {
            try FileManager.default.removeItem(at: markerURL)
        }
        _ = try await harnessCall("activate")
        _ = try await harnessCall("hideFakeChooser")
        _ = try await showPanelBalanced(
            directory: start.path,
            marker: markerName,
            expectedDirectory: destination.path
        )

        let context = try await makeSamplerContext()
        let telemetry = ComposerSamplerTelemetry()
        let outcome = await runCurrentComposerMonitor(bounds: PostconditionBounds.planTime) {
            await ComposerChooserSampler.sample(context: context, telemetry: telemetry)
        }
        let description = outcomeDescription(outcome)

        var navigationCandidates: [String] = []
        var reflected = false
        var confirmationAction: String?
        var navigationError: String?
        var pressError: String?
        let frontmost = await ensureHarnessFrontmostWithKeyPanel(timeoutSeconds: 8.0)
        let frontmostBundleIDAtInput = NSWorkspace.shared.frontmostApplication?.bundleIdentifier
        if frontmost, description.affirmed != nil {
            do {
                inputPostCount += 3
                navigationCandidates = try FolderChooserDriver.navigateToDestination(pid: harnessPID, destination: destination)
                reflected = FolderChooserDriver.destinationIsReflected(pid: harnessPID, destination: destination)
            } catch {
                navigationError = String(describing: error)
            }
            if navigationError == nil {
                do {
                    confirmationAction = try FolderChooserDriver.pressDefaultButton(pid: harnessPID, titles: ["開啟", "Open", "打開"])
                    axPressCount += 1
                } catch {
                    pressError = String(describing: error)
                }
            }
        } else {
            navigationError = "harness not frontmost with key panel, or chooser not affirmed"
        }

        let closed = await closePanelBalanced(timeoutSeconds: 12)
        await sleep(milliseconds: 500)
        let markerWritten = FileManager.default.fileExists(atPath: markerURL.path)
        let state = (try? await refreshState()) ?? [:]
        let selected = state["panelSelectedURL"] as? String
        let selectedMatches = selected.map { URL(fileURLWithPath: $0).standardizedFileURL.path == destination.standardizedFileURL.path } ?? false

        let record = ComposerDestinationRecord(
            destinationPath: destination.path,
            startingDirectoryPath: start.path,
            affirmationObserved: description.affirmed != nil,
            affirmationWindowID: description.affirmed?.windowID,
            harnessFrontmostAtInput: frontmost,
            frontmostBundleIDAtInput: frontmostBundleIDAtInput,
            navigationCandidates: navigationCandidates,
            destinationReflectedAfterNavigation: reflected,
            confirmationAction: confirmationAction ?? pressError.map { "refused: \($0)" } ?? navigationError.map { "noPress: \($0)" },
            axPressDispatchCount: axPressCount,
            keyboardPostsForConfirmation: 0,
            panelClosedEventObserved: closed != nil,
            markerFileName: markerName,
            markerWrittenAtDestination: markerWritten,
            panelSelectedURL: selected,
            panelSelectedMatchesDestination: selectedMatches,
            atISO8601: EvidenceIO.iso8601()
        )
        _ = try writeItem("05-destination-confirmation.json", record)
        return record
    }

    // MARK: item 6 — refusal and crash matrix

    private func refusalCase(
        caseID: String,
        scenario: String,
        expected: String,
        observedOutcome: String,
        observedDetail: String,
        affirmed: Bool,
        irreversible: Int,
        posts: Int,
        passed: Bool
    ) -> ComposerRefusalCaseRecord {
        ComposerRefusalCaseRecord(
            caseID: caseID,
            scenario: scenario,
            expected: expected,
            observedOutcome: observedOutcome,
            observedDetail: observedDetail,
            affirmed: affirmed,
            irreversibleDispatches: irreversible,
            inputPosts: posts,
            passed: passed
        )
    }

    private func itemRefusalMatrix() async throws -> ComposerRefusalMatrixRecord {
        var cases: [ComposerRefusalCaseRecord] = []
        let telemetry = ComposerSamplerTelemetry()

        // (1) Panel closed after reversible navigation: AXPress must refuse and
        // no confirmation may be consumed.
        do {
            let start = fixturesDir.appendingPathComponent("refusal-press-start")
            try EvidenceIO.ensureDirectory(start)
            _ = try await harnessCall("activate")
            _ = try await showPanelBalanced(
                directory: start.path,
                marker: "refusal-press.marker"
            )
            let context = try await makeSamplerContext()
            let outcome = await runCurrentComposerMonitor(bounds: PostconditionBounds.planTime) {
                await ComposerChooserSampler.sample(context: context, telemetry: telemetry)
            }
            let affirmed = outcomeDescription(outcome).affirmed != nil
            var detail = "chooser not affirmed; case not executed"
            var passed = false
            var presses = 0
            let postsBefore = inputPostCount
            if affirmed {
                let destination = fixturesDir.appendingPathComponent("refusal-press-destination")
                try EvidenceIO.ensureDirectory(destination)
                _ = try? FolderChooserDriver.navigateToDestination(pid: harnessPID, destination: destination)
                _ = await closePanelBalanced()
                await sleep(milliseconds: 300)
                do {
                    _ = try FolderChooserDriver.pressDefaultButton(pid: harnessPID, titles: ["開啟", "Open", "打開"])
                    detail = "AXPress unexpectedly succeeded after the panel was closed"
                    presses = 1
                } catch {
                    detail = "AXPress refused: \(error)"
                    passed = true
                }
            }
            cases.append(refusalCase(
                caseID: "press-refused-after-panel-closed",
                scenario: "destination preparation followed by panel loss before confirmation",
                expected: "pressDefaultButton refuses; exactly zero AXPress dispatches",
                observedOutcome: passed ? "refused" : "unexpected",
                observedDetail: detail,
                affirmed: false,
                irreversible: presses,
                posts: inputPostCount - postsBefore,
                passed: passed
            ))
        }

        // (2) Same-process look-alike chooser window.
        do {
            _ = try await harnessCall("activate")
            _ = try await harnessCall("showFakeChooser", params: ["dx": 60.0, "dy": 60.0])
            await sleep(milliseconds: 700)
            let context = try await makeSamplerContext()
            let sample = await ComposerChooserSampler.sample(context: context, telemetry: telemetry)
            let entry = (await telemetry.drain()).last
            let passed = sample.affirmed == nil
            cases.append(refusalCase(
                caseID: "same-process-lookalike-refused",
                scenario: "same-process window titled Open with a text field and two buttons",
                expected: "strict predicate must not affirm the look-alike",
                observedOutcome: passed ? "refused" : "affirmed",
                observedDetail: entry?.note ?? sample.note ?? "noNote",
                affirmed: sample.affirmed != nil,
                irreversible: 0,
                posts: inputPostCount,
                passed: passed
            ))
            _ = try await harnessCall("hideFakeChooser")
            await sleep(milliseconds: 300)
        }

        // (3) Separate-process look-alike chooser owned by the occluder.
        do {
            _ = try await occluderCall("lookalike", params: ["x": 420.0, "y": 260.0, "w": 420.0, "h": 220.0])
            await sleep(milliseconds: 700)
            let context = try await makeSamplerContext()
            let sample = await ComposerChooserSampler.sample(context: context, telemetry: telemetry)
            let entry = (await telemetry.drain()).last
            let passed = sample.affirmed == nil
            cases.append(refusalCase(
                caseID: "foreign-process-lookalike-refused",
                scenario: "separate-process occluder window titled Open",
                expected: "strict predicate must not affirm a foreign process surface",
                observedOutcome: passed ? "refused" : "affirmed",
                observedDetail: entry?.note ?? sample.note ?? "noNote",
                affirmed: sample.affirmed != nil,
                irreversible: 0,
                posts: inputPostCount,
                passed: passed
            ))
            _ = try await occluderCall("hideLookalike")
            await sleep(milliseconds: 300)
        }

        // (4) Harness crash mid-observation: observe-only, zero input.
        do {
            let start = fixturesDir.appendingPathComponent("refusal-crash-start")
            try EvidenceIO.ensureDirectory(start)
            _ = try await harnessCall("activate")
            _ = try await showPanelBalanced(
                directory: start.path,
                marker: "refusal-crash.marker"
            )
            let context = try await makeSamplerContext()
            let bounds = PostconditionBounds(
                fastCadenceMs: 60,
                fastPhaseSeconds: 0.6,
                slowCadenceMs: 120,
                hardCapSeconds: 1.2,
                lateForensicSampleDelaySeconds: 0.6
            )
            let postsBefore = inputPostCount
            let monitorTask = Task.detached {
                await runCurrentComposerMonitor(bounds: bounds) {
                    await ComposerChooserSampler.sample(context: context, telemetry: telemetry)
                }
            }
            await sleep(milliseconds: 250)
            harness?.terminate()
            let outcome = await monitorTask.value
            let description = outcomeDescription(outcome)
            let entry = (await telemetry.drain()).last
            let passed = description.affirmed == nil && (inputPostCount - postsBefore) == 0
            cases.append(refusalCase(
                caseID: "harness-crash-mid-observation-observe-only",
                scenario: "harness process terminated while the strict monitor was observing",
                expected: "no affirmation, zero further input, observe-only terminal",
                observedOutcome: description.name,
                observedDetail: entry?.note ?? "noNote",
                affirmed: description.affirmed != nil,
                irreversible: 0,
                posts: inputPostCount - postsBefore,
                passed: passed
            ))
        }

        let record = ComposerRefusalMatrixRecord(
            cases: cases,
            allPassed: cases.allSatisfy { $0.passed },
            atISO8601: EvidenceIO.iso8601()
        )
        _ = try writeItem("06-refusal-and-crash-matrix.json", record)
        return record
    }

    // MARK: run

    private func writeSHA256Sums() {
        do {
            var lines: [String] = []
            let resolvedRoot = runRoot.resolvingSymlinksInPath().path
            for directory in [itemsDir, logsDir] {
                let urls = (try? FileManager.default.contentsOfDirectory(at: directory, includingPropertiesForKeys: [.isRegularFileKey])) ?? []
                for url in urls.sorted(by: { $0.path < $1.path }) {
                    guard let data = try? Data(contentsOf: url) else { continue }
                    let resolved = url.resolvingSymlinksInPath().path
                    let relative = resolved.hasPrefix(resolvedRoot + "/")
                        ? String(resolved.dropFirst(resolvedRoot.count + 1))
                        : url.lastPathComponent
                    lines.append("\(EvidenceIO.sha256Hex(data))  \(relative)")
                }
            }
            try Data((lines.joined(separator: "\n") + "\n").utf8).write(
                to: runRoot.appendingPathComponent("sha256sums.txt"),
                options: .atomic
            )
        } catch {
            notes.append("SHA256SUMS_ERROR: \(error)")
        }
    }

    private func terminateChildren() {
        occluder?.terminate()
        harness?.terminate()
    }

    /// Environment precondition failure: this is not a partial product verdict,
    /// the run is blocked before any measurable item (session lock, activation
    /// refusal, prepare failure). Blocked runs never claim item results.
    private func finishBlocked(verdict: String, harnessBundleObserved: String?) -> Int32 {
        let record = ComposerApplicabilityVerdict(
            taskID: taskID,
            frozenBindings: frozenBindings,
            geometryRecheckPass: false,
            chooserCalibrationPass: false,
            strictMonitorTimingsPass: false,
            destinationConfirmationPass: false,
            refusalMatrixPass: false,
            harnessBundleIDObserved: harnessBundleObserved,
            harnessPID: harnessPID == 0 ? nil : harnessPID,
            realLineInteraction: "NONE",
            overallVerdict: verdict,
            blocker: notes.last,
            atISO8601: EvidenceIO.iso8601()
        )
        _ = try? writeItem("07-applicability-verdict.json", record)
        let summary = ComposerRunSummary(
            runRoot: runRoot.path,
            taskID: taskID,
            startedAtISO8601: ISO8601DateFormatter().string(from: atStart),
            durationSeconds: Date().timeIntervalSince(atStart),
            timingCount: options.timingCount,
            geometryPass: false,
            chooserPass: false,
            timingsPass: false,
            destinationPass: false,
            refusalsPass: false,
            overallVerdict: verdict,
            blocker: notes.last,
            notes: notes,
            inputPostsTotal: inputPostCount,
            axPressTotal: axPressCount
        )
        _ = try? writeItem("08-run-summary.json", summary)
        writeSHA256Sums()
        terminateChildren()
        FileHandle.standardOutput.write(Data("runID=\(runRoot.lastPathComponent) root=\(runRoot.path) verdict=\(verdict) blocker=\(notes.last ?? "?")\n".utf8))
        return 75
    }

    /// Diagnostic-only path (`--diagnose-only`): runs the sensor/locator/timing
    /// items the locked-session precondition would otherwise block, and can
    /// never claim PASS. Used to converge on driver defects without a live
    /// session; every record it writes is explicitly labelled DIAGNOSTIC_ONLY.
    private func runDiagnosticItems(harnessBundleObserved: String?) async -> Int32 {
        var geometryPass = false
        var chooserPass = false
        var timingsPass = false
        do {
            try await itemGeometryRecheck()
            let data = try Data(contentsOf: itemsDir.appendingPathComponent("02-geometry-recheck.json"))
            let record = try JSONDecoder().decode(ComposerGeometryRecord.self, from: data)
            geometryPass = record.allCellsValid && record.allMarkersWithinTolerance && record.cells.allSatisfy { $0.frozenRulePresent }
        } catch {
            notes.append("GEOMETRY_RECHECK_ERROR: \(error)")
        }
        do {
            try await itemChooserCalibration()
            if let data = try? Data(contentsOf: itemsDir.appendingPathComponent("03-chooser-ax-calibration.json")),
               let record = try? JSONDecoder().decode(ComposerChooserCalibrationRecord.self, from: data) {
                chooserPass = record.panelWindowFound && record.matchesFrozenCalibration && record.derivedPredicateID != nil
            }
        } catch {
            notes.append("CHOOSER_CALIBRATION_ERROR: \(error)")
        }
        do {
            try await itemStrictMonitorTimings()
            if let data = try? Data(contentsOf: itemsDir.appendingPathComponent("04-strict-monitor-timings.json")),
               let record = try? JSONDecoder().decode(ComposerMonitorTimingsRecord.self, from: data) {
                timingsPass = record.allAffirmedInWindow
                    && record.maxAffirmedBelowFastPhase
                    && record.timeoutCase?.outcome == "noChooserObserved"
                    && record.delayedCase?.outcome == "chooserVerified"
                    && record.lateCase?.outcome == "chooserObservedAfterWindow"
            }
        } catch {
            notes.append("STRICT_MONITOR_TIMINGS_ERROR: \(error)")
        }
        let verdict = ComposerApplicabilityVerdict(
            taskID: taskID,
            frozenBindings: frozenBindings,
            geometryRecheckPass: geometryPass,
            chooserCalibrationPass: chooserPass,
            strictMonitorTimingsPass: timingsPass,
            destinationConfirmationPass: false,
            refusalMatrixPass: false,
            harnessBundleIDObserved: harnessBundleObserved,
            harnessPID: harnessPID == 0 ? nil : harnessPID,
            realLineInteraction: "NONE",
            overallVerdict: "DIAGNOSTIC_ONLY",
            blocker: notes.last,
            atISO8601: EvidenceIO.iso8601()
        )
        _ = try? writeItem("07-applicability-verdict.json", verdict)
        let summary = ComposerRunSummary(
            runRoot: runRoot.path,
            taskID: taskID,
            startedAtISO8601: ISO8601DateFormatter().string(from: atStart),
            durationSeconds: Date().timeIntervalSince(atStart),
            timingCount: options.timingCount,
            geometryPass: geometryPass,
            chooserPass: chooserPass,
            timingsPass: timingsPass,
            destinationPass: false,
            refusalsPass: false,
            overallVerdict: "DIAGNOSTIC_ONLY",
            blocker: notes.last,
            notes: notes,
            inputPostsTotal: inputPostCount,
            axPressTotal: axPressCount
        )
        _ = try? writeItem("08-run-summary.json", summary)
        writeSHA256Sums()
        terminateChildren()
        FileHandle.standardOutput.write(Data("runID=\(runRoot.lastPathComponent) root=\(runRoot.path) verdict=DIAGNOSTIC_ONLY\n".utf8))
        return 0
    }

    func runAll() async -> Int32 {

        // The frozen harness driver initializes AppKit the same way before it
        // touches any CoreGraphics window API; without this a plain CLI process
        // aborts in CGS initialization on the first CGWindowList call.
        _ = NSApplication.shared

        // Hard precondition: a locked console session refuses activation, keeps
        // panels off the window server's on-screen list and blocks key-window
        // input, so every calibration item would measure the lock, not the
        // composer. Fail closed before spawning anything.
        let session = currentSessionRecord()
        _ = try? writeItem("00-session-state.json", session)
        let sessionBlocked = session.screenLocked || session.frontmostIsLoginWindow
        if sessionBlocked, options.diagnoseOnly {
            notes.append("SESSION_LOCKED_DIAGNOSTIC_BYPASS frontmost=\(session.frontmostBundleID ?? "nil")")
        } else if sessionBlocked {
            notes.append("SESSION_LOCKED frontmost=\(session.frontmostBundleID ?? "nil") onConsole=\(session.onConsole.map(String.init) ?? "?")")
            return finishBlocked(verdict: "BLOCKED_SESSION_LOCKED", harnessBundleObserved: nil)
        }

        var geometryPass = false
        var chooserPass = false
        var timingsPass = false
        var destinationPass = false
        var refusalsPass = false
        var harnessBundleObserved: String?
        do {
            try await prepareEnvironment()
        } catch {
            notes.append("PREPARE_ERROR: \(error)")
            return finishBlocked(verdict: "BLOCKED_PREPARE_FAILED", harnessBundleObserved: nil)
        }
        harnessBundleObserved = ProcessIdentity.bundleID(pid: harnessPID)
        if harnessBundleObserved != harnessBundleID {
            notes.append("HARNESS_BUNDLE_ID_MISMATCH observed=\(harnessBundleObserved ?? "nil") expected=\(harnessBundleID)")
        }
        let activated = await waitForHarnessActivation(timeoutSeconds: options.diagnoseOnly ? 3.0 : 8.0)
        if !activated, options.diagnoseOnly {
            notes.append("ACTIVATION_REFUSED_DIAGNOSTIC_BYPASS frontmost=\(NSWorkspace.shared.frontmostApplication?.bundleIdentifier ?? "nil")")
        } else if !activated {
            notes.append("HARNESS_ACTIVATION_REFUSED frontmost=\(NSWorkspace.shared.frontmostApplication?.bundleIdentifier ?? "nil")")
            return finishBlocked(verdict: "BLOCKED_ACTIVATION_REFUSED", harnessBundleObserved: harnessBundleObserved)
        }

        if options.diagnoseOnly {
            return await runDiagnosticItems(harnessBundleObserved: harnessBundleObserved)
        }

        do {
            try await itemGeometryRecheck()
            let data = try Data(contentsOf: itemsDir.appendingPathComponent("02-geometry-recheck.json"))
            let record = try JSONDecoder().decode(ComposerGeometryRecord.self, from: data)
            geometryPass = record.allCellsValid && record.allMarkersWithinTolerance && record.cells.allSatisfy { $0.frozenRulePresent }
        } catch {
            notes.append("GEOMETRY_RECHECK_ERROR: \(error)")
        }

        do {
            try await itemChooserCalibration()
            if let data = try? Data(contentsOf: itemsDir.appendingPathComponent("03-chooser-ax-calibration.json")),
               let record = try? JSONDecoder().decode(ComposerChooserCalibrationRecord.self, from: data) {
                chooserPass = record.panelWindowFound && record.matchesFrozenCalibration && record.derivedPredicateID != nil
            }
        } catch {
            notes.append("CHOOSER_CALIBRATION_ERROR: \(error)")
        }

        do {
            try await itemStrictMonitorTimings()
            if let data = try? Data(contentsOf: itemsDir.appendingPathComponent("04-strict-monitor-timings.json")),
               let record = try? JSONDecoder().decode(ComposerMonitorTimingsRecord.self, from: data) {
                timingsPass = record.allAffirmedInWindow
                    && record.maxAffirmedBelowFastPhase
                    && record.timeoutCase?.outcome == "noChooserObserved"
                    && record.delayedCase?.outcome == "chooserVerified"
                    && record.lateCase?.outcome == "chooserObservedAfterWindow"
                    && (record.lateCase?.affirmed ?? false)
            }
        } catch {
            notes.append("STRICT_MONITOR_TIMINGS_ERROR: \(error)")
        }

        do {
            let record = try await itemDestinationConfirmation()
            destinationPass = record.affirmationObserved
                && record.harnessFrontmostAtInput
                && record.destinationReflectedAfterNavigation
                && record.confirmationAction?.hasPrefix("role=AXButton") == true
                && record.axPressDispatchCount == 1
                && record.panelClosedEventObserved
                && record.markerWrittenAtDestination
                && record.panelSelectedMatchesDestination
        } catch {
            notes.append("DESTINATION_CONFIRMATION_ERROR: \(error)")
        }

        do {
            let record = try await itemRefusalMatrix()
            refusalsPass = record.allPassed
        } catch {
            notes.append("REFUSAL_MATRIX_ERROR: \(error)")
        }

        let allPass = geometryPass && chooserPass && timingsPass && destinationPass && refusalsPass
        let overallVerdict = allPass ? "PASS" : "PARTIAL"
        let verdict = ComposerApplicabilityVerdict(
            taskID: taskID,
            frozenBindings: frozenBindings,
            geometryRecheckPass: geometryPass,
            chooserCalibrationPass: chooserPass,
            strictMonitorTimingsPass: timingsPass,
            destinationConfirmationPass: destinationPass,
            refusalMatrixPass: refusalsPass,
            harnessBundleIDObserved: harnessBundleObserved,
            harnessPID: harnessPID == 0 ? nil : harnessPID,
            realLineInteraction: "NONE",
            overallVerdict: overallVerdict,
            blocker: allPass ? nil : notes.last,
            atISO8601: EvidenceIO.iso8601()
        )
        _ = try? writeItem("07-applicability-verdict.json", verdict)

        let summary = ComposerRunSummary(
            runRoot: runRoot.path,
            taskID: taskID,
            startedAtISO8601: ISO8601DateFormatter().string(from: atStart),
            durationSeconds: Date().timeIntervalSince(atStart),
            timingCount: options.timingCount,
            geometryPass: geometryPass,
            chooserPass: chooserPass,
            timingsPass: timingsPass,
            destinationPass: destinationPass,
            refusalsPass: refusalsPass,
            overallVerdict: overallVerdict,
            blocker: allPass ? nil : notes.last,
            notes: notes,
            inputPostsTotal: inputPostCount,
            axPressTotal: axPressCount
        )
        _ = try? writeItem("08-run-summary.json", summary)

        writeSHA256Sums()
        terminateChildren()
        FileHandle.standardOutput.write(Data("runID=\(runRoot.lastPathComponent) root=\(runRoot.path) verdict=\(overallVerdict)\n".utf8))
        return 0
    }
}
