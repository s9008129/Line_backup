import CoreGraphics
import Foundation

// MARK: - One common native composition (plan R4 §C2/C3/C5/C6)
//
// This adapter is the single production composition: it drives the existing
// LiveExecutionEngine state machine with fresh NativeObservationSession
// bundles, typed run-bound evidence, the reviewed structural locators, the
// frozen chooser predicate, StrictPostconditionMonitor, guarded Quartz
// actuation, GatedDestinationConfirmation, StagingVerifier and BaselineVerifier.
// It cannot declare a state valid by returning a digest: every transition
// writes and re-validates a NativeStateEvidence artifact.

public final class NativeLiveExecutionAdapter: @unchecked Sendable, LiveExecutionAdapter {
    public let configuration: NativeAdapterConfiguration
    private let observation: any ObservationBoundary
    private let actuation: any ActuationBoundary
    private let chooser: any ChooserBoundary
    private let filesystem: any FilesystemBoundary
    private let clock: any CompositionClock
    private let session: NativeObservationSession
    private let store: NativeEvidenceStore

    private let stateLock = NSLock()
    private var lastAlbumTitleBoxCapturePx: CGRect?
    private var lastGroupTitleBoxCapturePx: CGRect?
    private var lastMenuBoundsCapturePx: CGRect?
    private var lastAlbumCardCandidate: StructuralCandidate?
    private var lastChooserAffirmation: ChooserAffirmation?
    private var lastPreDispatchInventory: ObservationInventorySnapshot?
    private var downloadStartedAtUptime: Double?

    public init(
        configuration: NativeAdapterConfiguration,
        session: NativeObservationSession,
        store: NativeEvidenceStore,
        observation: any ObservationBoundary,
        actuation: any ActuationBoundary,
        chooser: any ChooserBoundary,
        filesystem: any FilesystemBoundary,
        clock: any CompositionClock
    ) throws {
        guard store.runDirectory == session.evidenceDirectory else {
            throw NativeAdapterError.precondition("evidence store and observation session run directories differ")
        }
        guard session.runID == store.runID else {
            throw NativeAdapterError.precondition("observation session and evidence store run IDs differ")
        }
        self.configuration = configuration
        self.session = session
        self.store = store
        self.observation = observation
        self.actuation = actuation
        self.chooser = chooser
        self.filesystem = filesystem
        self.clock = clock
    }

    // MARK: - LiveExecutionAdapter

    public func establish(state: ExecutionState, owner: PersistentTransactionOwner) async throws -> String {
        switch state {
        case .appReady: return try await establishAppReady(owner: owner)
        case .groupReady: return try await establishGroupReady(owner: owner)
        case .albumListReady: return try await establishAlbumListReady(owner: owner)
        case .targetAlbumLocated: return try await establishTargetAlbumLocated(owner: owner)
        case .albumDetailVerified: return try await establishAlbumDetailVerified(owner: owner)
        case .ellipsisLocated: return try await establishEllipsisLocated(owner: owner)
        case .menuVerified: return try await establishMenuVerified(owner: owner)
        case .saveAllLocated: return try await establishSaveAllLocated(owner: owner)
        default:
            throw NativeAdapterError.notAPreSaveState(state.rawValue)
        }
    }

    public func dispatchSaveAll(owner: PersistentTransactionOwner) async throws -> String {
        guard chooser.preDispatchContextSatisfied(minimumSeconds: 10) else {
            throw NativeAdapterError.dispatchRefused(
                "pre-dispatch tripwire context is missing, shorter than 10 seconds or unhealthy; zero irreversible intent"
            )
        }
        let bundle = try await freshBundle(state: .saveAllLocated, includeChildWindows: true, owner: owner)
        let candidate = try requireSaveAllCandidate(bundle: bundle, state: .saveAllLocated)
        try requireBaselineUnchanged(state: "SAVE_ALL_DISPATCH")
        let observationSnapshot = try await actuation.readinessObservation(identity: bundle.identity, candidate: candidate)
        let permit = try DispatchReadinessGate.mintPermit(
            identity: bundle.identity,
            candidate: candidate,
            observation: observationSnapshot,
            now: clock.monotonicNow()
        )
        let sink = actuation.clickSink()
        do {
            try GatedQuartzActuator.postClick(
                permit: permit,
                currentBinding: bundle.surfaceBinding,
                intent: .saveAll(owner),
                sink: sink,
                readinessCheck: { [actuation] pid, windowID in
                    actuation.revalidateDispatch(pid: pid, windowID: windowID, binding: bundle.surfaceBinding)
                },
                processIdentityCheck: { [actuation] pid, binding in
                    actuation.processStable(pid: pid, binding: binding)
                },
                postEventAccessCheck: { [actuation] in actuation.postEventAccess() },
                now: clock.monotonicNow()
            )
        } catch {
            throw NativeAdapterError.dispatchRefused("Save All dispatch refused: \(error)")
        }
        let counts = owner.irreversibleOperationCounts
        guard counts.saveAll == 2, counts.destinationConfirmation == 0 else {
            throw NativeAdapterError.dispatchRefused(
                "Save All boundary counts unexpected: saveAll=\(counts.saveAll) confirmation=\(counts.destinationConfirmation)"
            )
        }
        stateLock.lock()
        lastPreDispatchInventory = bundle.postInventory
        lastChooserAffirmation = nil
        downloadStartedAtUptime = nil
        stateLock.unlock()
        return try record(
            state: "SAVE_ALL_DISPATCH",
            bundle: bundle,
            facts: [
                "candidate": candidate.identity,
                "epoch": "\(bundle.epoch)",
                "frameSHA256": bundle.pngSHA256,
                "saveAllRecords": "\(counts.saveAll)",
                "confirmationRecords": "\(counts.destinationConfirmation)",
            ]
        )
    }

    public func observeChooser(owner: PersistentTransactionOwner) async throws -> LiveChooserEvidence {
        let preDispatchInventory: ObservationInventorySnapshot
        stateLock.lock()
        preDispatchInventory = lastPreDispatchInventory ?? ObservationInventorySnapshot(scWindows: [], cgWindows: [], sampledAtUptime: 0)
        stateLock.unlock()
        let predicate = configuration.chooserPredicate
        let chooserBoundary = chooser
        let verdict = await StrictPostconditionMonitor.run(
            bounds: .planTime,
            sampler: { [weak self] in
                guard let self else {
                    return .failed("adapter deallocated", tripwireObservations: [])
                }
                return await chooserBoundary.sample(preDispatchInventory: preDispatchInventory, predicate: predicate)
            },
            monotonicNow: { [clock] in clock.monotonicNow() },
            sleep: { [clock] seconds in await clock.sleep(seconds: seconds) }
        )
        let runDirectory = URL(fileURLWithPath: owner.authorization.evidenceRunDirectory)
        let tripwireFacts = Self.tripwireFacts(from: verdict)
        switch verdict {
        case let .chooserVerified(affirmation, _, tripwire):
            let postconditionURL = runDirectory.appendingPathComponent("native-postcondition.json")
            let tripwireURL = runDirectory.appendingPathComponent("native-tripwire.json")
            _ = try? FileManager.default.removeItem(at: postconditionURL)
            _ = try? FileManager.default.removeItem(at: tripwireURL)
            _ = try EvidenceIO.writeJSONAtomically(
                PostconditionEvidenceArtifact(runID: owner.authorization.runID, outcome: "CHOOSER_VERIFIED", chooserAffirmation: affirmation),
                to: postconditionURL,
                appendOnly: true
            )
            _ = try EvidenceIO.writeJSONAtomically(
                TripwireEvidenceArtifact(runID: owner.authorization.runID, observations: tripwireFacts),
                to: tripwireURL,
                appendOnly: true
            )
            stateLock.lock()
            lastChooserAffirmation = affirmation
            stateLock.unlock()
            let postconditionDigest = try BoundEvidenceDigest.load(
                fileURL: postconditionURL,
                withinRunDirectory: runDirectory,
                runID: owner.authorization.runID
            )
            let tripwireDigest = try BoundEvidenceDigest.load(
                fileURL: tripwireURL,
                withinRunDirectory: runDirectory,
                runID: owner.authorization.runID
            )
            _ = tripwire
            return LiveChooserEvidence(postcondition: postconditionDigest, tripwire: tripwireDigest)
        default:
            let outcome = Self.verdictName(verdict)
            let terminalURL = runDirectory.appendingPathComponent("native-chooser-terminal.json")
            _ = try? FileManager.default.removeItem(at: terminalURL)
            _ = try? EvidenceIO.writeJSONAtomically(
                PostconditionEvidenceArtifact(runID: owner.authorization.runID, outcome: outcome, chooserAffirmation: nil),
                to: terminalURL,
                appendOnly: true
            )
            throw NativeAdapterError.chooserTerminal(outcome)
        }
    }

    public func prepareDestination(owner: PersistentTransactionOwner) async throws -> String {
        let destination = URL(fileURLWithPath: owner.authorization.stagingRunDirectory)
        let affirmation = try requireChooserAffirmation()
        var facts: [String: String] = [
            "destination": destination.standardizedFileURL.path,
            "primitives": "\(DestinationPrimitive.allCases.count)",
        ]
        for primitive in DestinationPrimitive.allCases {
            guard chooser.panelStillBound(pid: affirmation.ownerPID, confirmation: affirmation) else {
                throw NativeAdapterError.destinationRefused("panel identity lost before primitive \(primitive.rawValue)")
            }
            do {
                try owner.recordReversibleDispatch(action: "destination.\(primitive.rawValue)")
            } catch {
                throw NativeAdapterError.destinationRefused("reversible budget refused primitive \(primitive.rawValue): \(error)")
            }
            do {
                let primitiveFacts = try chooser.preparePrimitive(primitive, pid: affirmation.ownerPID, destination: destination)
                for (key, value) in primitiveFacts {
                    facts["\(primitive.rawValue).\(key)"] = value
                }
            } catch {
                throw NativeAdapterError.destinationRefused("primitive \(primitive.rawValue) refused: \(error)")
            }
        }
        guard chooser.destinationReflected(pid: affirmation.ownerPID, destination: destination) else {
            throw NativeAdapterError.destinationRefused("reflected destination does not equal the authorized canonical staging path")
        }
        guard chooser.panelStillBound(pid: affirmation.ownerPID, confirmation: affirmation) else {
            throw NativeAdapterError.destinationRefused("panel identity lost after destination preparation")
        }
        facts["reversibleDispatches"] = "\(owner.reversibleDispatchCount)"
        let bundle = try await freshBundle(state: .destinationPrepared, includeChildWindows: true, owner: owner, requestedStateOverride: "DESTINATION_PREPARED")
        return try record(state: ExecutionState.destinationPrepared.rawValue, bundle: bundle, facts: facts)
    }

    public func confirmDestination(owner: PersistentTransactionOwner) async throws -> String {
        let affirmation = try requireChooserAffirmation()
        do {
            try GatedDestinationConfirmation.perform(
                owner: owner,
                action: "AXPressDefaultButton",
                readinessCheck: { [chooser] in
                    chooser.panelStillBound(pid: affirmation.ownerPID, confirmation: affirmation)
                },
                dispatch: { [chooser] in
                    _ = try chooser.pressDefaultButton(pid: affirmation.ownerPID, confirmation: affirmation)
                }
            )
        } catch {
            throw NativeAdapterError.dispatchRefused("destination confirmation refused: \(error)")
        }
        let counts = owner.irreversibleOperationCounts
        guard counts.saveAll == 2, counts.destinationConfirmation == 2 else {
            throw NativeAdapterError.dispatchRefused(
                "confirmation boundary counts unexpected: saveAll=\(counts.saveAll) confirmation=\(counts.destinationConfirmation)"
            )
        }
        let bundle = try await freshBundle(state: .downloadConfirmed, includeChildWindows: true, owner: owner, requestedStateOverride: "DESTINATION_CONFIRMATION")
        return try record(
            state: "DESTINATION_CONFIRMATION",
            bundle: bundle,
            facts: [
                "action": "AXPressDefaultButton",
                "saveAllRecords": "\(counts.saveAll)",
                "confirmationRecords": "\(counts.destinationConfirmation)",
                "predicateID": affirmation.predicateID,
            ]
        )
    }

    public func observeDownloadStarted(owner: PersistentTransactionOwner) async throws -> String {
        let affirmation = try requireChooserAffirmation()
        guard chooser.chooserClosed(pid: affirmation.ownerPID) else {
            throw NativeAdapterError.stagingTerminal("chooser surface still present after confirmation")
        }
        let destination = URL(fileURLWithPath: owner.authorization.stagingRunDirectory)
        guard filesystem.directoryExists(destination) else {
            throw NativeAdapterError.stagingTerminal("authorized staging directory does not exist after confirmation")
        }
        stateLock.lock()
        downloadStartedAtUptime = clock.monotonicNow()
        stateLock.unlock()
        let bundle = try await freshBundle(state: .downloadConfirmed, includeChildWindows: true, owner: owner)
        return try record(
            state: ExecutionState.downloadConfirmed.rawValue,
            bundle: bundle,
            facts: ["chooserClosed": "true", "stagingDirectory": destination.standardizedFileURL.path]
        )
    }

    public func observeDownloadInProgress(owner: PersistentTransactionOwner) async throws -> String {
        let destination = URL(fileURLWithPath: owner.authorization.stagingRunDirectory)
        guard filesystem.directoryExists(destination) else {
            throw NativeAdapterError.stagingTerminal("staging directory disappeared during download observation")
        }
        let snapshot = try filesystem.stagingSnapshot(directory: destination, observedAt: Date().timeIntervalSince1970)
        let bundle = try await freshBundle(state: .downloadInProgress, includeChildWindows: true, owner: owner)
        return try record(
            state: ExecutionState.downloadInProgress.rawValue,
            bundle: bundle,
            facts: [
                "fileCount": "\(snapshot.files.count)",
                "totalBytes": "\(snapshot.totalBytes)",
                "observedAt": "\(snapshot.observedAt)",
            ]
        )
    }

    public func observeFilesystemStable(owner: PersistentTransactionOwner) async throws -> String {
        let destination = URL(fileURLWithPath: owner.authorization.stagingRunDirectory)
        stateLock.lock()
        let startedAt = downloadStartedAtUptime
        stateLock.unlock()
        guard let startedAt else {
            throw NativeAdapterError.precondition("filesystem stability observed before confirmation boundary")
        }
        let deadline = startedAt + configuration.downloadObservationLimitSeconds
        var samples: [StagingSnapshot] = []
        while true {
            let now = clock.monotonicNow()
            if now > deadline {
                stateLock.lock()
                lastStableSampleCount = samples.count
                stateLock.unlock()
                throw NativeAdapterError.stagingTerminal(
                    "STAGING_UNSTABLE: download observation limit reached with \(samples.count) samples"
                )
            }
            let snapshot = try filesystem.stagingSnapshot(directory: destination, observedAt: Date().timeIntervalSince1970)
            samples.append(snapshot)
            if StagingVerifier.isStable(snapshots: samples) {
                let verification = StagingVerifier.verifyStableSnapshots(samples)
                stateLock.lock()
                lastSnapshotSamples = samples
                lastStableVerification = verification
                stateLock.unlock()
                let bundle = try await freshBundle(state: .filesystemStable, includeChildWindows: true, owner: owner)
                return try record(
                    state: ExecutionState.filesystemStable.rawValue,
                    bundle: bundle,
                    facts: [
                        "samples": "\(samples.count)",
                        "spanSeconds": "\(String(format: "%.3f", (samples.last?.observedAt ?? 0) - (samples.first?.observedAt ?? 0)))",
                        "fileCount": "\(verification.fileCount)",
                        "totalBytes": "\(verification.totalBytes)",
                        "stagingOutcome": verification.outcome.rawValue,
                    ]
                )
            }
            await clock.sleep(seconds: configuration.stagingSnapshotIntervalSeconds)
        }
    }

    public func verifyContent(owner: PersistentTransactionOwner) async throws -> LiveContentEvidence {
        let destination = URL(fileURLWithPath: owner.authorization.stagingRunDirectory)
        stateLock.lock()
        let samples = lastSnapshotSamples
        stateLock.unlock()
        let snapshot: StagingSnapshot
        if let last = samples?.last, StagingVerifier.isStable(snapshots: samples ?? []) {
            snapshot = last
        } else {
            snapshot = try filesystem.stagingSnapshot(directory: destination, observedAt: Date().timeIntervalSince1970)
        }
        let verification = StagingVerifier.verify(snapshot: snapshot)
        let baseline: BaselineVerificationResult
        do {
            baseline = try filesystem.verifyBaseline(referenceFile: configuration.baselineReferenceFileURL)
        } catch {
            throw NativeAdapterError.baselineRefused("baseline verification failed: \(error)")
        }
        let artifact = NativeContentEvidence(
            runID: owner.authorization.runID,
            outcome: verification.outcome.rawValue,
            fileCount: verification.fileCount,
            totalBytes: verification.totalBytes,
            contentMultisetSHA256: verification.contentMultisetSHA256,
            baselineContentMultisetSHA256: baseline.contentMultisetSHA256,
            baselineTripwireSHA256: baseline.nameInclusiveTripwireSHA256,
            detail: verification.detail
        )
        let artifactURL = store.runDirectory.appendingPathComponent("native-content-verification.json")
        let digest: String
        do {
            digest = try EvidenceIO.writeJSONAtomically(artifact, to: artifactURL, appendOnly: true)
        } catch EvidenceIOError.alreadyExists {
            let existing = try Data(contentsOf: artifactURL)
            digest = EvidenceIO.sha256Hex(existing)
        }
        return LiveContentEvidence(verification: verification, evidenceSHA256: digest)
    }

    // MARK: - Mutable state helpers

    private var lastSnapshotSamples: [StagingSnapshot]?
    private var lastStableVerification: StagingVerification?
    private var lastStableSampleCount = 0

    private func requireChooserAffirmation() throws -> ChooserAffirmation {
        stateLock.lock()
        defer { stateLock.unlock() }
        guard let affirmation = lastChooserAffirmation else {
            throw NativeAdapterError.precondition("chooser affirmation is unavailable; chooser state not established")
        }
        return affirmation
    }

    private func requireBaselineUnchanged(state: String) throws {
        do {
            _ = try filesystem.verifyBaseline(referenceFile: configuration.baselineReferenceFileURL)
        } catch {
            throw NativeAdapterError.baselineRefused("\(state): baseline verification failed: \(error)")
        }
    }

    // MARK: - Observation helpers

    private func freshBundle(
        state: ExecutionState,
        includeChildWindows: Bool,
        owner: PersistentTransactionOwner,
        requestedStateOverride: String? = nil
    ) async throws -> ObservationBundle {
        do {
            let bundle = try await session.observe(
                state: CaptureGeometryState(settled: true, activated: true, includeChildWindows: includeChildWindows, ignoreShadows: true),
                requestedState: requestedStateOverride ?? state.rawValue,
                timeoutSeconds: configuration.captureTimeoutSeconds
            )
            try ObservationBundleValidator.validate(
                bundle,
                expectedSessionID: session.sessionID,
                expectedRunID: owner.authorization.runID
            )
            try requireCensusFreshness(bundle, state: state)
            return bundle
        } catch let error as NativeAdapterError {
            throw error
        } catch {
            throw NativeAdapterError.stateRefused(state: state.rawValue, reason: "observation refused: \(error)")
        }
    }

    private func requireCensusFreshness(_ bundle: ObservationBundle, state: ExecutionState) throws {
        let scMatches = bundle.postInventory.scWindows.filter {
            $0.windowID == bundle.identity.windowID
                && $0.ownerPID == bundle.process.pid
                && $0.ownerBundleID == bundle.bundleID
                && $0.windowLayer == 0
                && $0.isOnScreen
                && abs(Double($0.frame.minX - bundle.identity.windowFrame.minX)) <= 0.5
                && abs(Double($0.frame.minY - bundle.identity.windowFrame.minY)) <= 0.5
                && abs(Double($0.frame.width - bundle.identity.windowFrame.width)) <= 0.5
                && abs(Double($0.frame.height - bundle.identity.windowFrame.height)) <= 0.5
        }
        guard scMatches.count == 1 else {
            throw NativeAdapterError.stateRefused(state: state.rawValue, reason: "fresh SC census matches=\(scMatches.count)")
        }
        let cgMatches = bundle.postInventory.cgWindows.filter {
            $0.windowNumber == bundle.identity.windowID && $0.ownerPID == bundle.process.pid && $0.layer == 0
        }
        guard cgMatches.count == 1 else {
            throw NativeAdapterError.stateRefused(state: state.rawValue, reason: "fresh CG census matches=\(cgMatches.count)")
        }
        guard ProcessInstanceID.current(pid: bundle.process.pid) == bundle.process else {
            throw NativeAdapterError.stateRefused(state: state.rawValue, reason: "process instance changed since capture")
        }
    }

    private func record(state: String, bundle: ObservationBundle, facts: [String: String]) throws -> String {
        do {
            return try store.record(state: state, bundle: bundle, facts: facts)
        } catch {
            throw NativeAdapterError.stateRefused(state: state, reason: "typed evidence refused: \(error)")
        }
    }

    // MARK: - Pre-Save-All states

    private func establishAppReady(owner: PersistentTransactionOwner) async throws -> String {
        let bundle = try await freshBundle(state: .appReady, includeChildWindows: false, owner: owner)
        guard bundle.bundleID == configuration.targetBundleID else {
            throw NativeAdapterError.stateRefused(state: ExecutionState.appReady.rawValue, reason: "bundle id mismatch")
        }
        guard let signingIdentity = bundle.signingIdentity, !signingIdentity.isEmpty else {
            throw NativeAdapterError.stateRefused(state: ExecutionState.appReady.rawValue, reason: "signing identity unavailable")
        }
        guard bundle.axEvidence.pid == bundle.process.pid,
              bundle.axEvidence.windowID == bundle.identity.windowID,
              bundle.axEvidence.role != nil else {
            throw NativeAdapterError.stateRefused(state: ExecutionState.appReady.rawValue, reason: "AX evidence is not bound to the captured window")
        }
        return try record(
            state: ExecutionState.appReady.rawValue,
            bundle: bundle,
            facts: [
                "bundleID": bundle.bundleID,
                "pid": "\(bundle.process.pid)",
                "windowID": "\(bundle.identity.windowID)",
                "signingIdentity": signingIdentity,
                "axRole": bundle.axEvidence.role ?? "nil",
                "captureStateKey": bundle.captureStateKey,
            ]
        )
    }

    private func establishGroupReady(owner: PersistentTransactionOwner) async throws -> String {
        let bundle = try await freshBundle(state: .groupReady, includeChildWindows: false, owner: owner)
        let matches = OcrTextIdentity.exactMatches(in: bundle.ocrItems, expected: configuration.targetGroup)
        guard matches.count == 1 else {
            throw NativeAdapterError.stateRefused(
                state: ExecutionState.groupReady.rawValue,
                reason: "exact group title matches=\(matches.count)"
            )
        }
        return try record(
            state: ExecutionState.groupReady.rawValue,
            bundle: bundle,
            facts: [
                "group": configuration.targetGroup,
                "groupBox": Self.rectString(matches[0].boundingBoxCapturePx),
            ]
        )
    }

    private func establishAlbumListReady(owner: PersistentTransactionOwner) async throws -> String {
        let bundle = try await freshBundle(state: .albumListReady, includeChildWindows: false, owner: owner)
        let regions = StructuralLocators.segmentAlbumCards(items: bundle.ocrItems, imageBounds: bundle.capturePixelBounds)
        guard !regions.isEmpty else {
            throw NativeAdapterError.stateRefused(state: ExecutionState.albumListReady.rawValue, reason: "no segmented album card regions")
        }
        let titles = OcrTextIdentity.exactMatches(in: bundle.ocrItems, expected: configuration.targetAlbumTitle)
        guard titles.count == 1 else {
            throw NativeAdapterError.stateRefused(
                state: ExecutionState.albumListReady.rawValue,
                reason: "exact album title matches=\(titles.count)"
            )
        }
        guard regions.contains(where: { $0.boundsCapturePx.contains(titles[0].boundingBoxCapturePx) }) else {
            throw NativeAdapterError.stateRefused(
                state: ExecutionState.albumListReady.rawValue,
                reason: "album title is not contained in a segmented card region"
            )
        }
        return try record(
            state: ExecutionState.albumListReady.rawValue,
            bundle: bundle,
            facts: [
                "regionCount": "\(regions.count)",
                "titleBox": Self.rectString(titles[0].boundingBoxCapturePx),
            ]
        )
    }

    private func establishTargetAlbumLocated(owner: PersistentTransactionOwner) async throws -> String {
        let bundle = try await freshBundle(state: .targetAlbumLocated, includeChildWindows: false, owner: owner)
        let regions = StructuralLocators.segmentAlbumCards(items: bundle.ocrItems, imageBounds: bundle.capturePixelBounds)
        let candidate = try requireAlbumCardCandidate(bundle: bundle, regions: regions, state: .targetAlbumLocated)
        stateLock.lock()
        lastAlbumCardCandidate = candidate
        stateLock.unlock()
        return try record(
            state: ExecutionState.targetAlbumLocated.rawValue,
            bundle: bundle,
            facts: [
                "candidate": candidate.identity,
                "point": "\(candidate.pointCapturePx.x),\(candidate.pointCapturePx.y)",
                "regions": "\(regions.count)",
            ]
        )
    }

    private func establishAlbumDetailVerified(owner: PersistentTransactionOwner) async throws -> String {
        let locateBundle = try await freshBundle(state: .albumDetailVerified, includeChildWindows: false, owner: owner)
        let regions = StructuralLocators.segmentAlbumCards(items: locateBundle.ocrItems, imageBounds: locateBundle.capturePixelBounds)
        let candidate = try requireAlbumCardCandidate(bundle: locateBundle, regions: regions, state: .albumDetailVerified)
        try performReversibleClick(
            bundle: locateBundle,
            candidate: candidate,
            action: "openAlbumCard",
            owner: owner
        )
        await clock.sleep(seconds: 0.5)
        let bundle = try await freshBundle(state: .albumDetailVerified, includeChildWindows: false, owner: owner)
        guard case .success = StructuralLocators.verifyAlbumDetail(
            items: bundle.ocrItems,
            groupTitle: configuration.targetGroup,
            countText: configuration.targetPhotoCountText
        ) else {
            throw NativeAdapterError.stateRefused(
                state: ExecutionState.albumDetailVerified.rawValue,
                reason: "album detail group/count continuity not proven"
            )
        }
        let titles = OcrTextIdentity.exactMatches(in: bundle.ocrItems, expected: configuration.targetAlbumTitle)
        guard titles.count == 1 else {
            throw NativeAdapterError.stateRefused(
                state: ExecutionState.albumDetailVerified.rawValue,
                reason: "exact album title matches=\(titles.count) on detail surface"
            )
        }
        let groupMatches = OcrTextIdentity.exactMatches(in: bundle.ocrItems, expected: configuration.targetGroup)
        stateLock.lock()
        lastAlbumTitleBoxCapturePx = titles[0].boundingBoxCapturePx
        lastGroupTitleBoxCapturePx = groupMatches.first?.boundingBoxCapturePx
        stateLock.unlock()
        return try record(
            state: ExecutionState.albumDetailVerified.rawValue,
            bundle: bundle,
            facts: [
                "albumTitleBox": Self.rectString(titles[0].boundingBoxCapturePx),
                "countText": configuration.targetPhotoCountText,
                "reversibleDispatches": "\(owner.reversibleDispatchCount)",
            ]
        )
    }

    private func establishEllipsisLocated(owner: PersistentTransactionOwner) async throws -> String {
        let locateBundle = try await freshBundle(state: .ellipsisLocated, includeChildWindows: false, owner: owner)
        let titles = OcrTextIdentity.exactMatches(in: locateBundle.ocrItems, expected: configuration.targetAlbumTitle)
        guard titles.count == 1 else {
            throw NativeAdapterError.stateRefused(
                state: ExecutionState.ellipsisLocated.rawValue,
                reason: "exact album title matches=\(titles.count)"
            )
        }
        let image = try locateBundle.decodedRetainedImage()
        let result: StructuralLocatorResult
        do {
            result = try AlbumEllipsisLocator.locate(
                image: image,
                ocrItems: locateBundle.ocrItems,
                titleBoxCapturePx: titles[0].boundingBoxCapturePx,
                binding: locateBundle.surfaceBinding
            )
        } catch {
            throw NativeAdapterError.stateRefused(
                state: ExecutionState.ellipsisLocated.rawValue,
                reason: "ellipsis pixel detection failed: \(error)"
            )
        }
        guard case let .candidate(candidate) = result else {
            if case let .refused(refusal, detail) = result {
                throw NativeAdapterError.stateRefused(
                    state: ExecutionState.ellipsisLocated.rawValue,
                    reason: "ellipsis refused \(refusal.rawValue): \(detail)"
                )
            }
            throw NativeAdapterError.stateRefused(state: ExecutionState.ellipsisLocated.rawValue, reason: "ellipsis not located")
        }
        try performReversibleClick(bundle: locateBundle, candidate: candidate, action: "openAlbumMenu", owner: owner)
        await clock.sleep(seconds: 0.5)
        stateLock.lock()
        lastAlbumTitleBoxCapturePx = titles[0].boundingBoxCapturePx
        stateLock.unlock()
        return try record(
            state: ExecutionState.ellipsisLocated.rawValue,
            bundle: locateBundle,
            facts: [
                "candidate": candidate.identity,
                "point": "\(candidate.pointCapturePx.x),\(candidate.pointCapturePx.y)",
                "reversibleDispatches": "\(owner.reversibleDispatchCount)",
            ]
        )
    }

    private func establishMenuVerified(owner: PersistentTransactionOwner) async throws -> String {
        let bundle = try await freshBundle(state: .menuVerified, includeChildWindows: true, owner: owner)
        let rows = try requireMenuRows(bundle: bundle, state: .menuVerified)
        guard let menuBounds = Self.menuBounds(rows: rows, imageBounds: bundle.capturePixelBounds) else {
            throw NativeAdapterError.stateRefused(state: ExecutionState.menuVerified.rawValue, reason: "menu bounds are not addressable")
        }
        stateLock.lock()
        lastMenuBoundsCapturePx = menuBounds
        stateLock.unlock()
        return try record(
            state: ExecutionState.menuVerified.rawValue,
            bundle: bundle,
            facts: [
                "rows": rows.map(\.text).joined(separator: "|"),
                "menuBounds": Self.rectString(menuBounds),
            ]
        )
    }

    private func establishSaveAllLocated(owner: PersistentTransactionOwner) async throws -> String {
        let bundle = try await freshBundle(state: .saveAllLocated, includeChildWindows: true, owner: owner)
        let candidate = try requireSaveAllCandidate(bundle: bundle, state: .saveAllLocated)
        stateLock.lock()
        lastMenuBoundsCapturePx = candidate.safeRectCapturePx
        stateLock.unlock()
        return try record(
            state: ExecutionState.saveAllLocated.rawValue,
            bundle: bundle,
            facts: [
                "candidate": candidate.identity,
                "safeRect": Self.rectString(candidate.safeRectCapturePx),
                "point": "\(candidate.pointCapturePx.x),\(candidate.pointCapturePx.y)",
            ]
        )
    }

    // MARK: - Perception helpers

    private func requireAlbumCardCandidate(
        bundle: ObservationBundle,
        regions: [AlbumCardRegion],
        state: ExecutionState
    ) throws -> StructuralCandidate {
        switch StructuralLocators.locateAlbumCard(
            items: bundle.ocrItems,
            title: configuration.targetAlbumTitle,
            count: configuration.targetAlbumCardCountText,
            regions: regions,
            binding: bundle.surfaceBinding
        ) {
        case let .candidate(candidate):
            return candidate
        case let .refused(refusal, detail):
            throw NativeAdapterError.stateRefused(
                state: state.rawValue,
                reason: "album card refused \(refusal.rawValue): \(detail)"
            )
        }
    }

    private func requireMenuRows(bundle: ObservationBundle, state: ExecutionState) throws -> [MenuRowObservation] {
        var rows: [MenuRowObservation] = []
        for text in configuration.menuReferenceRows {
            let matches = OcrTextIdentity.exactMatches(in: bundle.ocrItems, expected: text)
            guard matches.count == 1 else {
                throw NativeAdapterError.stateRefused(
                    state: state.rawValue,
                    reason: "menu row '\(text)' exact matches=\(matches.count)"
                )
            }
            rows.append(MenuRowObservation(text: text, bandCapturePx: matches[0].boundingBoxCapturePx))
        }
        let sorted = rows.sorted { $0.bandCapturePx.midY < $1.bandCapturePx.midY }
        guard sorted.map(\.text) == configuration.menuReferenceRows else {
            throw NativeAdapterError.stateRefused(state: state.rawValue, reason: "menu row order does not match the reviewed reference")
        }
        return sorted
    }

    private func requireSaveAllCandidate(bundle: ObservationBundle, state: ExecutionState) throws -> StructuralCandidate {
        let rows = try requireMenuRows(bundle: bundle, state: state)
        guard let menuBounds = Self.menuBounds(rows: rows, imageBounds: bundle.capturePixelBounds) else {
            throw NativeAdapterError.stateRefused(state: state.rawValue, reason: "menu bounds are not addressable")
        }
        switch StructuralLocators.locateSaveAll(
            rows: rows,
            menuBounds: menuBounds,
            addressableBounds: bundle.capturePixelBounds,
            binding: bundle.surfaceBinding
        ) {
        case let .candidate(candidate):
            return candidate
        case let .refused(refusal, detail):
            throw NativeAdapterError.stateRefused(
                state: state.rawValue,
                reason: "Save All refused \(refusal.rawValue): \(detail)"
            )
        }
    }

    private func performReversibleClick(
        bundle: ObservationBundle,
        candidate: StructuralCandidate,
        action: String,
        owner: PersistentTransactionOwner
    ) throws {
        let readiness: ReadinessObservation
        do {
            readiness = try QuartzActuatorSyncBridge.readiness(
                actuation: actuation,
                identity: bundle.identity,
                candidate: candidate
            )
        } catch {
            throw NativeAdapterError.dispatchRefused("reversible \(action) readiness refused: \(error)")
        }
        let permit: ReadinessPermit
        do {
            permit = try DispatchReadinessGate.mintPermit(
                identity: bundle.identity,
                candidate: candidate,
                observation: readiness,
                now: clock.monotonicNow()
            )
        } catch {
            throw NativeAdapterError.dispatchRefused("reversible \(action) permit refused: \(error)")
        }
        let sink = actuation.clickSink()
        do {
            try GatedQuartzActuator.postClick(
                permit: permit,
                currentBinding: bundle.surfaceBinding,
                intent: .reversible(owner, action: action),
                sink: sink,
                readinessCheck: { [actuation] pid, windowID in
                    actuation.revalidateDispatch(pid: pid, windowID: windowID, binding: bundle.surfaceBinding)
                },
                processIdentityCheck: { [actuation] pid, binding in
                    actuation.processStable(pid: pid, binding: binding)
                },
                postEventAccessCheck: { [actuation] in actuation.postEventAccess() },
                now: clock.monotonicNow()
            )
        } catch {
            throw NativeAdapterError.dispatchRefused("reversible \(action) refused: \(error)")
        }
    }

    private static func menuBounds(rows: [MenuRowObservation], imageBounds: CGRect) -> CGRect? {
        guard let first = rows.first else { return nil }
        let union = rows.dropFirst().reduce(first.bandCapturePx) { $0.union($1.bandCapturePx) }
        guard !union.isNull, union.width > 0, union.height > 0 else { return nil }
        let expanded = union.insetBy(dx: -2, dy: -2)
        let clipped = expanded.intersection(imageBounds)
        guard !clipped.isNull, clipped.width >= 8, clipped.height >= 8 else { return nil }
        return clipped
    }

    private static func rectString(_ rect: CGRect) -> String {
        String(
            format: "%.2f,%.2f,%.2f,%.2f",
            Double(rect.minX), Double(rect.minY), Double(rect.width), Double(rect.height)
        )
    }

    private static func verdictName(_ verdict: StrictPostconditionVerdict) -> String {
        switch verdict {
        case .chooserVerified: return "CHOOSER_VERIFIED"
        case .noChooserObserved: return "CHOOSER_REFUSED_NO_OBSERVATION"
        case .chooserObservedAfterWindow: return "CHOOSER_OBSERVED_AFTER_WINDOW"
        case .tripwireAborted: return "TRIPWIRE_ABORTED"
        case .observerFailed: return "CHOOSER_OBSERVER_FAILED"
        case .deadlineExceeded: return "CHOOSER_DEADLINE_EXCEEDED"
        }
    }

    private static func tripwireFacts(from verdict: StrictPostconditionVerdict) -> [TripwireEvidenceFact] {
        let classifications: [TripwireClassification]
        switch verdict {
        case let .chooserVerified(_, _, tripwire): classifications = tripwire
        case let .noChooserObserved(_, tripwire): classifications = tripwire
        case let .chooserObservedAfterWindow(_, _, tripwire): classifications = tripwire
        case let .tripwireAborted(_, tripwire): classifications = tripwire
        case let .observerFailed(_, _, tripwire): classifications = tripwire
        case let .deadlineExceeded(_, tripwire): classifications = tripwire
        }
        return classifications.map { classification in
            let attributable = classification.outcome == .stagingExpectedEvidence
                || classification.outcome == .attributedExternalWriteObserved
                || classification.outcome == .abortedWriteOutsideApprovedRoot
            return TripwireEvidenceFact(
                occurredBeforeChooser: classification.outcome == .preDispatchContext,
                isWrite: attributionIsWrite(classification),
                attributableToThisRun: attributable,
                aborts: classification.aborts
            )
        }
    }

    private static func attributionIsWrite(_ classification: TripwireClassification) -> Bool {
        switch classification.outcome {
        case .environmentalContext, .preDispatchContext:
            return false
        default:
            return true
        }
    }
}

// MARK: - Actuation bridging

private enum QuartzActuatorSyncBridge {
    static func readiness(
        actuation: any ActuationBoundary,
        identity: WindowIdentity,
        candidate: StructuralCandidate
    ) throws -> ReadinessObservation {
        let semaphore = DispatchSemaphore(value: 0)
        var result: Result<ReadinessObservation, Error>?
        Task.detached {
            do {
                let observation = try await actuation.readinessObservation(identity: identity, candidate: candidate)
                result = .success(observation)
            } catch {
                result = .failure(error)
            }
            semaphore.signal()
        }
        semaphore.wait()
        switch result {
        case let .success(observation): return observation
        case let .failure(error): throw error
        case nil: throw NativeAdapterError.precondition("readiness observation did not complete")
        }
    }
}

public struct NativeContentEvidence: Codable, Equatable, Sendable {
    public let runID: String
    public let outcome: String
    public let fileCount: Int
    public let totalBytes: UInt64
    public let contentMultisetSHA256: String?
    public let baselineContentMultisetSHA256: String
    public let baselineTripwireSHA256: String
    public let detail: String

    public init(
        runID: String,
        outcome: String,
        fileCount: Int,
        totalBytes: UInt64,
        contentMultisetSHA256: String?,
        baselineContentMultisetSHA256: String,
        baselineTripwireSHA256: String,
        detail: String
    ) {
        self.runID = runID
        self.outcome = outcome
        self.fileCount = fileCount
        self.totalBytes = totalBytes
        self.contentMultisetSHA256 = contentMultisetSHA256
        self.baselineContentMultisetSHA256 = baselineContentMultisetSHA256
        self.baselineTripwireSHA256 = baselineTripwireSHA256
        self.detail = detail
    }
}
