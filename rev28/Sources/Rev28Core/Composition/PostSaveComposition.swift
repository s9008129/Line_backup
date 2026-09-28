import CoreGraphics
import Foundation

// MARK: - Composed post-Save-All capabilities (plan C5-C7)
//
// The adapter's post-Save-All methods keep every decision (state, predicate,
// intent, evidence validity) in common code. The PostSaveEnvironment only
// observes the machine and posts the reviewed AX/navigation primitives; tests
// substitute below those decisions. No production Save All can be dispatched
// without an explicitly validated Phase B eligibility artifact: this AB round
// arms none, so live-execute fails closed at the boundary.

final class PostSaveJournalBox: @unchecked Sendable {
    private let lock = NSLock()
    private var preCensus: ChooserCensus?
    private var boundCandidate: ChooserCandidate?
    private var boundWindowIDs: [UInt32] = []
    private var samples: [StagingSnapshot] = []
    private var lastDetailValue: String?
    private var confirmationMonotonic: Double?
    private var preDispatchContext: BoundEvidenceDigest?

    func recordPreCensus(_ census: ChooserCensus) {
        lock.lock(); preCensus = census; lock.unlock()
    }

    var recordedPreCensus: ChooserCensus? {
        lock.lock(); defer { lock.unlock() }
        return preCensus
    }

    func recordChooser(candidate: ChooserCandidate, windowIDs: [UInt32]) {
        lock.lock(); boundCandidate = candidate; boundWindowIDs = windowIDs; lock.unlock()
    }

    var boundChooser: (candidate: ChooserCandidate, windowIDs: [UInt32])? {
        lock.lock(); defer { lock.unlock() }
        guard let boundCandidate else { return nil }
        return (boundCandidate, boundWindowIDs)
    }

    func recordDetail(_ detail: String) {
        lock.lock(); lastDetailValue = detail; lock.unlock()
    }

    var lastDetail: String? {
        lock.lock(); defer { lock.unlock() }
        return lastDetailValue
    }

    func recordPreDispatchContext(_ digest: BoundEvidenceDigest) {
        lock.lock(); preDispatchContext = digest; lock.unlock()
    }

    var recordedPreDispatchContext: BoundEvidenceDigest? {
        lock.lock(); defer { lock.unlock() }
        return preDispatchContext
    }

    func recordSample(_ snapshot: StagingSnapshot) {
        lock.lock(); samples.append(snapshot); lock.unlock()
    }

    var snapshotsSoFar: [StagingSnapshot] {
        lock.lock(); defer { lock.unlock() }
        return samples
    }

    func recordConfirmation(at monotonic: Double) {
        lock.lock(); confirmationMonotonic = monotonic; lock.unlock()
    }

    var confirmationStart: Double? {
        lock.lock(); defer { lock.unlock() }
        return confirmationMonotonic
    }
}

extension ComposedNativeAdapter {
    /// Ten minutes from confirmation, per plan C7: automatic download
    /// observation stops there and preserves the incomplete/unstable terminal.
    public static let downloadObservationCapSeconds: Double = 600
    /// Plan C7 / Phase A: at least ten seconds of pre-dispatch environmental
    /// context at SAVE_ALL_LOCATED, with the tripwire running and gap-free.
    public static let minimumPreDispatchContextSeconds: Double = 10

    // MARK: - C7 pre-dispatch environmental context

    /// Records the ≥10-second pre-dispatch environmental context at
    /// SAVE_ALL_LOCATED. This is the Phase A capability (`live-preflight` calls
    /// it after the observation chain) and the immediate-pre-dispatch gate the
    /// Save All path runs before any irreversible intent. Zero irreversible
    /// intent: it posts nothing and consumes no entitlement.
    @discardableResult
    public func observePreDispatchContext(owner: PersistentTransactionOwner) async throws -> String {
        guard owner.currentState == .saveAllLocated else {
            throw ComposedAdapterError.stateRefused(
                state: "SAVE_ALL_LOCATED",
                detail: "pre-dispatch environmental context requires the durable SAVE_ALL_LOCATED state"
            )
        }
        let runDirectory = URL(fileURLWithPath: owner.authorization.evidenceRunDirectory)
        let stamp = EvidenceIO.iso8601().replacingOccurrences(of: ":", with: "-")
        let facts: PreDispatchContextFacts
        do {
            facts = try await postSave.preDispatchContext(minimumSeconds: Self.minimumPreDispatchContextSeconds)
        } catch {
            let record = PreDispatchContextRefusalRecord(
                runID: owner.authorization.runID,
                detail: String(describing: error),
                recordedAtISO8601: EvidenceIO.iso8601()
            )
            try? EvidenceIO.writeJSONAtomically(
                record,
                to: runDirectory.appendingPathComponent("pre-dispatch-context-refused-\(stamp).json")
            )
            throw ComposedAdapterError.stateRefused(
                state: "SAVE_ALL_LOCATED",
                detail: "pre-dispatch environmental context is not intact: \(error)"
            )
        }
        guard facts.isClean else {
            let record = PreDispatchContextRefusalRecord(
                runID: owner.authorization.runID,
                detail: facts.refusalDetail,
                recordedAtISO8601: EvidenceIO.iso8601()
            )
            try? EvidenceIO.writeJSONAtomically(
                record,
                to: runDirectory.appendingPathComponent("pre-dispatch-context-refused-\(stamp).json")
            )
            throw ComposedAdapterError.stateRefused(
                state: "SAVE_ALL_LOCATED",
                detail: facts.refusalDetail
            )
        }
        // The journal stays cumulative: this record is a disclosure snapshot,
        // never a drain, so the chooser/tripwire artifacts still carry the
        // pre-dispatch environmental facts.
        let record = PreDispatchContextRecord(
            runID: owner.authorization.runID,
            minimumSeconds: facts.minimumSeconds,
            observedSeconds: facts.observedSeconds,
            journalStartedAtMonotonicNanos: facts.journalStartedAtMonotonicNanos,
            collectionGap: facts.collectionGap,
            factCount: facts.facts.count,
            facts: facts.facts,
            recordedAtISO8601: EvidenceIO.iso8601()
        )
        let url = runDirectory.appendingPathComponent("pre-dispatch-context-\(stamp).json")
        try EvidenceIO.writeJSONAtomically(record, to: url)
        let digest = try BoundEvidenceDigest.load(
            fileURL: url,
            withinRunDirectory: runDirectory,
            runID: owner.authorization.runID
        )
        journalBox.recordPreDispatchContext(digest)
        return digest.sha256
    }

    // MARK: - C5 guarded Save All dispatch

    public func dispatchSaveAll(owner: PersistentTransactionOwner) async throws -> String {
        guard owner.currentState == .saveAllLocated else {
            throw ComposedAdapterError.stateRefused(
                state: "SAVE_ALL_LOCATED",
                detail: "Save All dispatch requires the durable SAVE_ALL_LOCATED state"
            )
        }
        guard let eligibility = phaseBEligibility else {
            throw ComposedAdapterError.stateRefused(
                state: "SAVE_ALL_LOCATED",
                detail: "Phase B eligibility artifact is not armed; no Save All dispatch is authorized in this round"
            )
        }
        let slot = try GoalSlot.load(directory: owner.goalSlotDirectory, authorization: owner.authorization)
        try eligibility.validate(
            against: owner.authorization,
            entitlementConsumed: slot?.entitlementConsumed ?? false
        )

        // The context gate runs immediately before the dispatch, so the
        // recorded window is the freshest possible one (plan C7: the journal
        // must be active with ≥10 s of context and no collection gaps).
        let preDispatchContextSHA256 = try await observePreDispatchContext(owner: owner)

        let bundle = try await observe(
            state: .saveAllLocated,
            owner: owner,
            localization: localization(for: .saveAllLocated)
        )
        guard try evaluate(state: .saveAllLocated, bundle: bundle), let candidate = bundle.candidate else {
            throw ComposedAdapterError.stateRefused(
                state: "SAVE_ALL_LOCATED",
                detail: "fresh observation no longer locates the Save All row"
            )
        }
        // C7: the baseline is re-verified immediately before the dispatch.
        let baseline = try postSave.verifyBaseline()
        guard baseline.nameInclusiveTripwireSHA256 == owner.authorization.baselineTripwireSHA256 else {
            throw ComposedAdapterError.stateRefused(
                state: "SAVE_ALL_LOCATED",
                detail: "baseline tripwire digest differs from the authorization"
            )
        }
        // The pre-dispatch census is captured before any event is posted, so a
        // later sample can never fabricate its own "pre" inventory.
        let census = try await postSave.preDispatchCensus()
        guard !census.isEmpty else {
            throw ComposedAdapterError.stateRefused(
                state: "SAVE_ALL_LOCATED",
                detail: "pre-dispatch census is empty; chooser affirmation would widen to refusal"
            )
        }
        let observation = try await environment.readinessObservation(identity: bundle.window, candidate: candidate)
        let permit = try DispatchReadinessGate.mintPermit(
            identity: bundle.window,
            candidate: candidate,
            observation: observation,
            now: environment.uptime()
        )
        journalBox.recordPreCensus(census)
        let runDirectory = URL(fileURLWithPath: owner.authorization.evidenceRunDirectory)
        let preCensusRecord = ChooserPreCensusRecord(
            runID: owner.authorization.runID,
            epoch: bundle.epoch,
            windowID: bundle.window.windowID,
            candidateIdentity: candidate.identity,
            frameSHA256: bundle.frame.imageSHA256,
            windowIDs: census.windowIDs,
            ownerPIDs: census.processes.map(\.pid),
            recordedAtMonotonicNanos: census.recordedAtMonotonicNanos
        )
        try EvidenceIO.writeJSONAtomically(
            preCensusRecord,
            to: runDirectory.appendingPathComponent("chooser-pre-census-\(bundle.epoch).json")
        )
        postSave.markDispatchBoundary()
        try postSave.dispatchSaveAllClick(
            owner: owner,
            permit: permit,
            binding: bundle.surfaceBinding
        )
        let counts = owner.irreversibleOperationCounts
        let record = SaveAllDispatchRecord(
            runID: owner.authorization.runID,
            windowID: bundle.window.windowID,
            candidateIdentity: candidate.identity,
            frameSHA256: bundle.frame.imageSHA256,
            epoch: bundle.epoch,
            saveAllRecords: counts.saveAll,
            destinationRecords: counts.destinationConfirmation,
            preDispatchContextSHA256: preDispatchContextSHA256,
            dispatchedAtISO8601: EvidenceIO.iso8601()
        )
        let data = try JSONEncoder().encode(record)
        try data.write(to: runDirectory.appendingPathComponent("saveAll-dispatch-\(bundle.epoch).json"))
        return EvidenceIO.sha256Hex(data)
    }

    // MARK: - C6 chooser affirmation

    public func observeChooser(owner: PersistentTransactionOwner) async throws -> LiveChooserEvidence {
        guard let census = journalBox.recordedPreCensus else {
            throw ComposedAdapterError.stateRefused(
                state: "CHOOSER_VERIFIED",
                detail: "pre-dispatch census is missing; the chooser cannot be affirmed"
            )
        }
        let predicate = configuration.chooserPredicate
        let adapter = self
        let verdict = await StrictPostconditionMonitor.run(
            bounds: .planTime,
            sampler: { @Sendable in
                switch await adapter.postSave.sampleChooserFacts(preCensus: census) {
                case let .failed(detail, tripwire):
                    return .failed(detail, tripwireObservations: tripwire)
                case let .facts(facts):
                    let evaluation = adapter.evaluateChooserCandidates(
                        facts: facts,
                        preCensus: census,
                        predicate: predicate
                    )
                    adapter.journalBox.recordDetail(evaluation.detail)
                    if let candidate = evaluation.candidate, let affirmation = evaluation.affirmation {
                        adapter.journalBox.recordChooser(candidate: candidate, windowIDs: [candidate.windowID])
                    }
                    return .observed(StrictPostconditionSample(
                        affirmation: evaluation.affirmation,
                        tripwireObservations: facts.tripwire
                    ))
                }
            },
            monotonicNow: { adapter.postSave.monotonicNow() },
            sleep: { seconds in await adapter.postSave.sleep(seconds: seconds) }
        )

        let runDirectory = URL(fileURLWithPath: owner.authorization.evidenceRunDirectory)
        let name = "chooser-\(EvidenceIO.iso8601().replacingOccurrences(of: ":", with: "-"))"
        func write(
            outcome: String,
            affirmation: ChooserAffirmation?,
            tripwire: [TripwireClassification]
        ) throws -> LiveChooserEvidence {
            let postcondition = PostconditionEvidenceArtifact(
                runID: owner.authorization.runID,
                outcome: outcome,
                chooserAffirmation: affirmation
            )
            let tripwireArtifact = TripwireEvidenceArtifact(
                runID: owner.authorization.runID,
                observations: Self.tripwireFacts(tripwire)
            )
            let postconditionURL = runDirectory.appendingPathComponent("\(name)-postcondition.json")
            let tripwireURL = runDirectory.appendingPathComponent("\(name)-tripwire.json")
            try EvidenceIO.writeJSONAtomically(postcondition, to: postconditionURL)
            try EvidenceIO.writeJSONAtomically(tripwireArtifact, to: tripwireURL)
            return LiveChooserEvidence(
                postcondition: try BoundEvidenceDigest.load(
                    fileURL: postconditionURL,
                    withinRunDirectory: runDirectory,
                    runID: owner.authorization.runID
                ),
                tripwire: try BoundEvidenceDigest.load(
                    fileURL: tripwireURL,
                    withinRunDirectory: runDirectory,
                    runID: owner.authorization.runID
                )
            )
        }

        switch verdict {
        case let .chooserVerified(affirmation, _, tripwire):
            return try write(outcome: "CHOOSER_VERIFIED", affirmation: affirmation, tripwire: tripwire)
        case let .chooserObservedAfterWindow(affirmation, _, tripwire):
            _ = try write(outcome: "CHOOSER_OBSERVED_AFTER_WINDOW", affirmation: affirmation, tripwire: tripwire)
            throw ComposedAdapterError.stateRefused(
                state: "CHOOSER_VERIFIED",
                detail: "chooser was first affirmed after the 15-second window; zero further input"
            )
        case let .noChooserObserved(_, tripwire):
            _ = try write(outcome: "NO_CHOOSER_OBSERVED", affirmation: nil, tripwire: tripwire)
            throw ComposedAdapterError.stateRefused(
                state: "CHOOSER_VERIFIED",
                detail: "no chooser affirmed inside the 15-second cap (\(journalBox.lastDetail ?? "no candidate detail"))"
            )
        case let .tripwireAborted(_, tripwire):
            _ = try write(outcome: "TRIPWIRE_ABORTED", affirmation: nil, tripwire: tripwire)
            throw ComposedAdapterError.stateRefused(
                state: "CHOOSER_VERIFIED",
                detail: "tripwire classified an aborting filesystem observation"
            )
        case let .observerFailed(detail, _, tripwire):
            _ = try write(outcome: "OBSERVER_FAILED", affirmation: nil, tripwire: tripwire)
            throw ComposedAdapterError.stateRefused(
                state: "CHOOSER_VERIFIED",
                detail: "chooser observer failed: \(detail)"
            )
        case let .deadlineExceeded(_, tripwire):
            _ = try write(outcome: "DEADLINE_EXCEEDED", affirmation: nil, tripwire: tripwire)
            throw ComposedAdapterError.stateRefused(
                state: "CHOOSER_VERIFIED",
                detail: "chooser observation exceeded its deadline"
            )
        }
    }

    func evaluateChooserCandidates(
        facts: ChooserFacts,
        preCensus: ChooserCensus,
        predicate: ChooserAffirmationPredicate
    ) -> (affirmation: ChooserAffirmation?, candidate: ChooserCandidate?, detail: String) {
        let prePIDs = preCensus.processes.map(\.pid)
        var affirmed: [(ChooserCandidate, ChooserAffirmation)] = []
        var refusals: [String] = []
        for window in facts.windows {
            let candidate = ChooserCandidate(
                windowID: window.windowID,
                frame: window.frame,
                onScreen: window.onScreen,
                presentInSCInventory: window.presentInSCInventory,
                presentInCGInventory: window.presentInCGInventory,
                isNewRelativeToPreDispatchInventory: !preCensus.windowIDs.contains(window.windowID),
                owner: window.owner,
                pidReuseDetected: window.pidReuseDetected,
                axNodes: window.axNodes,
                preDispatchCensusPIDs: prePIDs,
                postDispatchCensusPIDs: facts.postDispatchCensusPIDs,
                preDispatchOwner: window.preDispatchOwner,
                postDispatchOwner: window.postDispatchOwner
            )
            switch ChooserAffirmationEvaluator.evaluateProduction(candidate: candidate, predicate: predicate) {
            case .affirmed:
                affirmed.append((
                    candidate,
                    ChooserAffirmation(
                        windowID: window.windowID,
                        frame: window.frame,
                        ownerPID: window.owner.pid,
                        predicateID: predicate.predicateID,
                        affirmedAtISO8601: EvidenceIO.iso8601()
                    )
                ))
            case let .refused(cause, detail):
                if !preCensus.windowIDs.contains(window.windowID) {
                    refusals.append("\(cause.rawValue): \(detail)")
                }
            }
        }
        if affirmed.count == 1 {
            return (affirmed[0].1, affirmed[0].0, "affirmed")
        }
        if affirmed.count > 1 {
            return (nil, nil, "ambiguous: \(affirmed.count) windows satisfy the production predicate")
        }
        return (nil, nil, refusals.last ?? "no new window satisfied the production predicate")
    }

    static func tripwireFacts(_ classifications: [TripwireClassification]) -> [TripwireEvidenceFact] {
        classifications.map { classification in
            TripwireEvidenceFact(
                occurredBeforeChooser: classification.outcome == .preDispatchContext,
                isWrite: true,
                attributableToThisRun: classification.outcome == .stagingExpectedEvidence
                    || classification.outcome == .attributedExternalWriteObserved,
                aborts: classification.aborts
            )
        }
    }

    // MARK: - C6 destination preparation and one confirmation

    public func prepareDestination(owner: PersistentTransactionOwner) async throws -> String {
        let bound = try requireBoundChooser(state: "DESTINATION_PREPARED")
        let destination = URL(fileURLWithPath: owner.authorization.stagingRunDirectory)
        let observed = try postSave.prepareDestination(
            owner: owner,
            pid: bound.candidate.owner.pid,
            expectedProcess: Self.processInstance(of: bound.candidate.owner),
            destination: destination,
            predicate: configuration.chooserPredicate,
            candidate: bound.candidate
        )
        let record = DestinationPreparationRecord(
            runID: owner.authorization.runID,
            windowID: bound.candidate.windowID,
            destination: destination.path,
            observed: observed,
            preparedAtISO8601: EvidenceIO.iso8601()
        )
        let data = try JSONEncoder().encode(record)
        try data.write(
            to: URL(fileURLWithPath: owner.authorization.evidenceRunDirectory)
                .appendingPathComponent("destination-prepared-\(bound.candidate.windowID).json")
        )
        return EvidenceIO.sha256Hex(data)
    }

    public func confirmDestination(owner: PersistentTransactionOwner) async throws -> String {
        let bound = try requireBoundChooser(state: "DESTINATION_PREPARED")
        let destination = URL(fileURLWithPath: owner.authorization.stagingRunDirectory)
        let pressed = try postSave.confirmDefaultButton(
            owner: owner,
            pid: bound.candidate.owner.pid,
            expectedProcess: Self.processInstance(of: bound.candidate.owner),
            destination: destination,
            predicate: configuration.chooserPredicate,
            candidate: bound.candidate
        )
        journalBox.recordConfirmation(at: postSave.monotonicNow())
        let counts = owner.irreversibleOperationCounts
        let record = DestinationConfirmationRecord(
            runID: owner.authorization.runID,
            windowID: bound.candidate.windowID,
            destination: destination.path,
            pressed: pressed,
            saveAllRecords: counts.saveAll,
            destinationRecords: counts.destinationConfirmation,
            confirmedAtISO8601: EvidenceIO.iso8601()
        )
        let data = try JSONEncoder().encode(record)
        try data.write(
            to: URL(fileURLWithPath: owner.authorization.evidenceRunDirectory)
                .appendingPathComponent("destination-confirmed-\(bound.candidate.windowID).json")
        )
        return EvidenceIO.sha256Hex(data)
    }

    // MARK: - C7 download observation, filesystem proof, content

    public func observeDownloadStarted(owner: PersistentTransactionOwner) async throws -> String {
        let bound = try requireBoundChooser(state: "DOWNLOAD_CONFIRMED")
        let stagingDirectory = URL(fileURLWithPath: owner.authorization.stagingRunDirectory)
        guard let facts = await postSave.postConfirmationFacts(
            chooserWindowIDs: bound.windowIDs,
            stagingDirectory: stagingDirectory
        ) else {
            throw ComposedAdapterError.stateRefused(
                state: "DOWNLOAD_CONFIRMED",
                detail: "post-confirmation observation failed; zero further input"
            )
        }
        let record = DownloadStartRecord(
            runID: owner.authorization.runID,
            chooserClosed: !facts.chooserWindowStillOnScreen,
            fileCount: facts.stagingSnapshot.files.count,
            totalBytes: facts.stagingSnapshot.totalBytes,
            tripwireAborts: facts.tripwire.filter(\.aborts).count,
            recordedAtISO8601: EvidenceIO.iso8601()
        )
        let data = try JSONEncoder().encode(record)
        try data.write(
            to: URL(fileURLWithPath: owner.authorization.evidenceRunDirectory)
                .appendingPathComponent("download-started.json")
        )
        if facts.tripwire.contains(where: \.aborts) {
            throw ComposedAdapterError.stateRefused(
                state: "DOWNLOAD_CONFIRMED",
                detail: "tripwire classified an aborting filesystem observation after confirmation"
            )
        }
        guard !facts.chooserWindowStillOnScreen else {
            throw ComposedAdapterError.stateRefused(
                state: "DOWNLOAD_CONFIRMED",
                detail: "the affirmed chooser window is still on screen; download start is not confirmed"
            )
        }
        journalBox.recordSample(facts.stagingSnapshot)
        return EvidenceIO.sha256Hex(data)
    }

    public func observeDownloadInProgress(owner: PersistentTransactionOwner) async throws -> String {
        let stagingDirectory = URL(fileURLWithPath: owner.authorization.stagingRunDirectory)
        let confirmationStart = journalBox.confirmationStart ?? postSave.monotonicNow()
        var polls = 0
        while true {
            let elapsed = postSave.monotonicNow() - confirmationStart
            if elapsed > Self.downloadObservationCapSeconds {
                let verification = StagingVerifier.verifyStableSnapshots(journalBox.snapshotsSoFar)
                let record = DownloadProgressRecord(
                    runID: owner.authorization.runID,
                    polls: polls,
                    elapsedSeconds: elapsed,
                    stable: false,
                    terminal: verification.outcome == .stagingUnstable ? "STAGING_UNSTABLE" : "STAGING_INCOMPLETE",
                    fileCount: journalBox.snapshotsSoFar.last?.files.count ?? 0,
                    recordedAtISO8601: EvidenceIO.iso8601()
                )
                let data = try JSONEncoder().encode(record)
                try data.write(
                    to: URL(fileURLWithPath: owner.authorization.evidenceRunDirectory)
                        .appendingPathComponent("download-progress-terminal.json")
                )
                throw ComposedAdapterError.stateRefused(
                    state: "DOWNLOAD_IN_PROGRESS",
                    detail: "automatic download observation stopped at the 10-minute cap with \(record.terminal ?? "UNKNOWN")"
                )
            }
            journalBox.recordSample(try postSave.stagingSnapshot(directory: stagingDirectory))
            polls += 1
            if StagingVerifier.isStable(snapshots: journalBox.snapshotsSoFar) { break }
            await postSave.sleep(seconds: 1.0)
        }
        let snapshots = journalBox.snapshotsSoFar
        let record = DownloadProgressRecord(
            runID: owner.authorization.runID,
            polls: polls,
            elapsedSeconds: postSave.monotonicNow() - confirmationStart,
            stable: true,
            terminal: nil,
            fileCount: snapshots.last?.files.count ?? 0,
            recordedAtISO8601: EvidenceIO.iso8601()
        )
        let data = try JSONEncoder().encode(record)
        try data.write(
            to: URL(fileURLWithPath: owner.authorization.evidenceRunDirectory)
                .appendingPathComponent("download-progress.json")
        )
        return EvidenceIO.sha256Hex(data)
    }

    public func observeFilesystemStable(owner: PersistentTransactionOwner) async throws -> String {
        let snapshots = journalBox.snapshotsSoFar
        guard StagingVerifier.isStable(snapshots: snapshots), let last = snapshots.last else {
            throw ComposedAdapterError.stateRefused(
                state: "FILESYSTEM_STABLE",
                detail: "staging snapshots are not stable at the stability gate"
            )
        }
        let record = FilesystemStableRecord(
            runID: owner.authorization.runID,
            samples: snapshots.count,
            fileCount: last.files.count,
            totalBytes: last.totalBytes,
            recordedAtISO8601: EvidenceIO.iso8601()
        )
        let data = try JSONEncoder().encode(record)
        try data.write(
            to: URL(fileURLWithPath: owner.authorization.evidenceRunDirectory)
                .appendingPathComponent("filesystem-stable.json")
        )
        return EvidenceIO.sha256Hex(data)
    }

    public func verifyContent(owner: PersistentTransactionOwner) async throws -> LiveContentEvidence {
        let snapshots = journalBox.snapshotsSoFar
        let verification = StagingVerifier.verifyStableSnapshots(snapshots)
        let baseline = try postSave.verifyBaseline()
        guard baseline.nameInclusiveTripwireSHA256 == owner.authorization.baselineTripwireSHA256 else {
            throw ComposedAdapterError.stateRefused(
                state: "CONTENT_VERIFIED",
                detail: "accepted baseline changed during the run; aborting without a success claim"
            )
        }
        let record = ContentVerificationRecord(
            runID: owner.authorization.runID,
            verification: verification,
            baselineTripwireSHA256: baseline.nameInclusiveTripwireSHA256,
            baselineUnchanged: true,
            recordedAtISO8601: EvidenceIO.iso8601()
        )
        let data = try JSONEncoder().encode(record)
        try data.write(
            to: URL(fileURLWithPath: owner.authorization.evidenceRunDirectory)
                .appendingPathComponent("content-verification.json")
        )
        return LiveContentEvidence(verification: verification, evidenceSHA256: EvidenceIO.sha256Hex(data))
    }

    private func requireBoundChooser(state: String) throws -> (candidate: ChooserCandidate, windowIDs: [UInt32]) {
        guard let bound = journalBox.boundChooser else {
            throw ComposedAdapterError.stateRefused(
                state: state,
                detail: "no affirmed chooser candidate is bound to this process"
            )
        }
        return bound
    }

    static func processInstance(of facts: ChooserProcessFacts) -> ProcessInstanceID {
        let start = facts.startTimeUnix ?? 0
        let seconds = Int64(start.rounded(.down))
        let microseconds = Int32(((start - Double(seconds)) * 1_000_000.0).rounded())
        return ProcessInstanceID(pid: facts.pid, startTimeSeconds: seconds, startTimeMicroseconds: microseconds)
    }
}

// MARK: - Durable post-Save-All records

struct ChooserPreCensusRecord: Codable {
    let runID: String
    let epoch: UInt64
    let windowID: UInt32
    let candidateIdentity: String
    let frameSHA256: String
    let windowIDs: [UInt32]
    let ownerPIDs: [Int32]
    let recordedAtMonotonicNanos: UInt64
}

struct SaveAllDispatchRecord: Codable {
    let runID: String
    let windowID: UInt32
    let candidateIdentity: String
    let frameSHA256: String
    let epoch: UInt64
    let saveAllRecords: Int
    let destinationRecords: Int
    let preDispatchContextSHA256: String
    let dispatchedAtISO8601: String
}

struct PreDispatchContextRecord: Codable {
    let runID: String
    let minimumSeconds: Double
    let observedSeconds: Double
    let journalStartedAtMonotonicNanos: UInt64
    let collectionGap: String?
    let factCount: Int
    let facts: [TripwireJournalFact]
    let recordedAtISO8601: String
}

struct PreDispatchContextRefusalRecord: Codable {
    let runID: String
    let detail: String
    let recordedAtISO8601: String
}

struct DestinationPreparationRecord: Codable {
    let runID: String
    let windowID: UInt32
    let destination: String
    let observed: String
    let preparedAtISO8601: String
}

struct DestinationConfirmationRecord: Codable {
    let runID: String
    let windowID: UInt32
    let destination: String
    let pressed: String
    let saveAllRecords: Int
    let destinationRecords: Int
    let confirmedAtISO8601: String
}

struct DownloadStartRecord: Codable {
    let runID: String
    let chooserClosed: Bool
    let fileCount: Int
    let totalBytes: UInt64
    let tripwireAborts: Int
    let recordedAtISO8601: String
}

struct DownloadProgressRecord: Codable {
    let runID: String
    let polls: Int
    let elapsedSeconds: Double
    let stable: Bool
    let terminal: String?
    let fileCount: Int
    let recordedAtISO8601: String
}

struct FilesystemStableRecord: Codable {
    let runID: String
    let samples: Int
    let fileCount: Int
    let totalBytes: UInt64
    let recordedAtISO8601: String
}

struct ContentVerificationRecord: Codable {
    let runID: String
    let verification: StagingVerification
    let baselineTripwireSHA256: String
    let baselineUnchanged: Bool
    let recordedAtISO8601: String
}
