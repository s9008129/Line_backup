import CoreGraphics
import Foundation
import XCTest
@testable import Rev28Core

final class AdversarialMatrixTests: XCTestCase {
    private let process = ProcessInstanceID(pid: 100, startTimeSeconds: 1_000, startTimeMicroseconds: 0)

    private func identity(epoch: UInt64 = 1) -> WindowIdentity {
        WindowIdentity(
            bundleID: "jp.naver.line.mac",
            process: process,
            windowID: 10,
            windowFrame: CGRect(x: 10, y: 20, width: 327, height: 643),
            ax: AXIdentityRead(role: "AXWindow", subrole: "AXStandardWindow", title: nil),
            cgEntry: CGWindowEntryRecord(
                windowID: 10,
                frame: CGRect(x: 10, y: 20, width: 327, height: 643),
                layer: 0,
                ownerPID: 100,
                ownerName: "LINE"
            ),
            captureEpoch: epoch,
            captureImageSHA256: String(repeating: "a", count: 64)
        )
    }

    private func fresh(
        bundle: String = "jp.naver.line.mac",
        pid: Int32 = 100,
        start: Int64 = 1_000,
        windowID: UInt32 = 10,
        frame: CGRect = CGRect(x: 10, y: 20, width: 327, height: 643),
        layer: Int = 0,
        onScreen: Bool = true
    ) -> FreshWindowObservation {
        FreshWindowObservation(
            bundleID: bundle,
            process: ProcessInstanceID(pid: pid, startTimeSeconds: start, startTimeMicroseconds: 0),
            windowID: windowID,
            frame: frame,
            layer: layer,
            isOnScreen: onScreen
        )
    }

    private func ocr(_ text: String, _ rect: CGRect) -> OcrItem {
        OcrItem(
            text: text,
            confidence: 1,
            candidateCount: 1,
            quadCapturePx: [
                CapturePixelPoint(x: rect.minX, y: rect.minY),
                CapturePixelPoint(x: rect.maxX, y: rect.minY),
                CapturePixelPoint(x: rect.minX, y: rect.maxY),
                CapturePixelPoint(x: rect.maxX, y: rect.maxY),
            ],
            boundingBoxCapturePx: rect
        )
    }

    private var binding: SurfaceBinding {
        SurfaceBinding(windowID: 10, captureEpoch: 1, frameSHA256: String(repeating: "a", count: 64))
    }

    private func rows() -> [MenuRowObservation] {
        StructuralLocators.lineAlbumMenuReference.enumerated().map {
            MenuRowObservation(text: $0.element, bandCapturePx: CGRect(x: 40, y: 20 + CGFloat($0.offset) * 50, width: 140, height: 24))
        }
    }

    // G01 wrong window
    func testG01WrongWindowRefused() {
        let violations = WindowIdentityValidator.validate(identity: identity(), against: fresh(windowID: 11), maxFrameDeltaPt: 1, currentEpoch: 1)
        XCTAssertTrue(violations.contains { if case .windowIDChanged = $0 { return true }; return false })
    }

    // G02 wrong bundle
    func testG02WrongBundleRefused() {
        let violations = WindowIdentityValidator.validate(identity: identity(), against: fresh(bundle: "com.example.fake"), maxFrameDeltaPt: 1, currentEpoch: 1)
        XCTAssertTrue(violations.contains { if case .bundleMismatch = $0 { return true }; return false })
    }

    // G03 stale windowID / epoch
    func testG03StaleEpochRefused() {
        let violations = WindowIdentityValidator.validate(identity: identity(epoch: 1), against: fresh(), maxFrameDeltaPt: 1, currentEpoch: 2)
        XCTAssertTrue(violations.contains { if case .staleEpoch = $0 { return true }; return false })
    }

    // G04 wrong Retina scale
    func testG04WrongRetinaScaleRefused() {
        XCTAssertNotNil(CaptureGeometryRules.validateScale(pointPixelScale: 2, backingScaleFactor: 1))
    }

    // G05 another app occludes target
    func testG05SeparateProcessOccluderBlocksDispatch() {
        XCTAssertEqual(
            DispatchReadinessEvaluator.refusal(for: DispatchReadiness(applicationActive: true, targetFrontmost: false, identityFresh: true, candidateFresh: true, geometrySafe: true)),
            .targetNotFrontmost
        )
    }

    // G06 window moves
    func testG06WindowMovementInvalidatesIdentity() {
        let moved = fresh(frame: CGRect(x: 25, y: 20, width: 327, height: 643))
        let violations = WindowIdentityValidator.validate(identity: identity(), against: moved, maxFrameDeltaPt: 1, currentEpoch: 1)
        XCTAssertTrue(violations.contains { if case .frameDeltaExceedsTolerance = $0 { return true }; return false })
    }

    // G07 popup moves after detection
    func testG07PopupMovementInvalidatesCandidateBinding() {
        let candidate = StructuralCandidate(identity: "儲存全部", safeRectCapturePx: CGRect(x: 0, y: 0, width: 10, height: 10), pointCapturePx: CapturePixelPoint(x: 5, y: 5), binding: binding)
        let moved = SurfaceBinding(windowID: 10, captureEpoch: 2, frameSHA256: String(repeating: "b", count: 64))
        guard case let .refused(reason, _) = StructuralLocators.revalidate(candidate: candidate, against: moved) else { return XCTFail("must refuse") }
        XCTAssertEqual(reason, .staleBinding)
    }

    // G08 wrong menu row
    func testG08WrongRowRefused() {
        var observed = rows()
        observed[2] = MenuRowObservation(text: "刪除相簿", bandCapturePx: observed[2].bandCapturePx)
        guard case let .refused(reason, _) = StructuralLocators.locateSaveAll(rows: observed, menuBounds: CGRect(x: 20, y: 10, width: 220, height: 270), addressableBounds: CGRect(x: 20, y: 10, width: 90, height: 270), binding: binding) else { return XCTFail("must refuse") }
        XCTAssertEqual(reason, .referenceStructureMismatch)
    }

    // G09 duplicate OCR target
    func testG09DuplicateOCRRefused() {
        var observed = rows()
        observed[3] = MenuRowObservation(text: "儲存全部", bandCapturePx: observed[3].bandCapturePx)
        guard case let .refused(reason, _) = StructuralLocators.locateSaveAll(rows: observed, menuBounds: CGRect(x: 20, y: 10, width: 220, height: 270), addressableBounds: CGRect(x: 20, y: 10, width: 90, height: 270), binding: binding) else { return XCTFail("must refuse") }
        XCTAssertEqual(reason, .ambiguousIdentity)
    }

    // G10 single-glyph corruption
    func testG10SingleGlyphCorruptionRefused() {
        let result = StructuralLocators.verifyAlbumDetail(
            items: [
                ocr("旻謙允楨成長日記", CGRect(x: 0, y: 0, width: 120, height: 20)),
                ocr("57張照片", CGRect(x: 0, y: 30, width: 60, height: 20)),
            ],
            groupTitle: "旻謙允禎成長日記"
        )
        guard case let .failure(error) = result else { return XCTFail("must refuse") }
        XCTAssertEqual(error.refusal, .missingIdentity)
    }

    // G11 whole-screen false positive outside popup
    func testG11WholeScreenFalsePositiveOutsidePopupRefused() {
        let shifted = rows().map { MenuRowObservation(text: $0.text, bandCapturePx: $0.bandCapturePx.offsetBy(dx: 500, dy: 0)) }
        guard case let .refused(reason, _) = StructuralLocators.locateSaveAll(rows: shifted, menuBounds: CGRect(x: 20, y: 10, width: 220, height: 270), addressableBounds: CGRect(x: 20, y: 10, width: 90, height: 270), binding: binding) else { return XCTFail("must refuse") }
        XCTAssertEqual(reason, .unsafeGeometry)
    }

    // G12 click outside popup
    func testG12OutsideSafeRegionIsNotDispatchable() {
        XCTAssertFalse(CaptureGeometryRules.isDispatchable(point: WindowLocalPoint(x: 101, y: 50), safeRect: CGRect(x: 0, y: 0, width: 100, height: 100)))
    }

    // G13 neighboring row
    func testG13SaveAllCandidateStaysInsideTargetStructuralCell() {
        guard case let .candidate(candidate) = StructuralLocators.locateSaveAll(rows: rows(), menuBounds: CGRect(x: 20, y: 10, width: 220, height: 270), addressableBounds: CGRect(x: 20, y: 10, width: 90, height: 270), binding: binding) else { return XCTFail("expected candidate") }
        XCTAssertLessThan(candidate.pointCapturePx.y, rows()[3].bandCapturePx.minY)
        XCTAssertGreaterThan(candidate.pointCapturePx.y, rows()[1].bandCapturePx.maxY)
    }

    // G14 focus theft
    func testG14FocusTheftBlocksDispatch() {
        XCTAssertEqual(
            DispatchReadinessEvaluator.refusal(for: DispatchReadiness(applicationActive: false, targetFrontmost: true, identityFresh: true, candidateFresh: true, geometrySafe: true)),
            .applicationInactive
        )
    }

    // G15 postcondition timeout
    func testG15PostconditionTimeoutIsNamedAndDoesNotRetry() async {
        final class Clock: @unchecked Sendable {
            let lock = NSLock(); var value = 0.0
            func now() -> Double { lock.lock(); defer { lock.unlock() }; return value }
            func add(_ x: Double) { lock.lock(); value += x; lock.unlock() }
        }
        let clock = Clock()
        let outcome = await PostconditionMonitor.run(
            bounds: PostconditionBounds(fastCadenceMs: 100, fastPhaseSeconds: 0.2, slowCadenceMs: 100, hardCapSeconds: 0.3, lateForensicSampleDelaySeconds: 0.1),
            sampler: { .notAffirmed },
            monotonicNow: { clock.now() },
            sleep: { clock.add($0) }
        )
        guard case .noChooserObserved = outcome else { return XCTFail("expected named timeout") }
    }

    // G16 fake chooser
    func testG16ExistingWindowCannotMasqueradeAsNewChooser() {
        let clauses = ChooserAXClauseSet(windowRole: "AXWindow", allowedSubroles: ["AXStandardWindow"], requiresTextField: false, textFieldRoles: [], requiresPopUpButton: false, popUpButtonRoles: [], defaultButton: nil, cancelButton: nil, requiresPathAffordance: false, pathAffordanceRoles: [], pathAffordanceTitles: [])
        let predicate = ChooserAffirmationPredicate(
            predicateID: "test", frozenAtISO8601: "x", calibratedAgainst: "test",
            ax: clauses,
            ownership: ChooserOwnershipClauseSet(requiresOwningPIDInCensusUnion: true, requiresStableProcessInstance: true, emptyPreCensusWidensRefusal: true)
        )
        let candidate = ChooserCandidate(
            windowID: 5, frame: .zero, onScreen: true, presentInSCInventory: true, presentInCGInventory: true,
            isNewRelativeToPreDispatchInventory: false,
            owner: ChooserProcessFacts(pid: 100, bundleID: "app", signingIdentity: nil, startTimeUnix: 1),
            pidReuseDetected: false,
            axNodes: [], preDispatchCensusPIDs: [100], postDispatchCensusPIDs: [100]
        )
        XCTAssertEqual(ChooserAffirmationEvaluator.evaluate(candidate: candidate, predicate: predicate), .refused(cause: .notNewWindow, detail: "candidate window is not new relative to the pre-dispatch inventory"))
    }

    // G17 unexpected filesystem write
    func testG17UnattributedL2WriteFailsClosed() {
        let root = URL(fileURLWithPath: "/tmp/root")
        let scope = TripwireScope(stagingRunDir: root.appendingPathComponent("run"), approvedRoot: root)
        let event = TripwireEvent(path: root.appendingPathComponent("other/file"), phase: .postDispatch, attributableToThisRun: false)
        let c = TripwireClassifier.classify(event: event, scope: scope)
        XCTAssertEqual(c.outcome, .abortedUnattributedFilesystemWrite)
        XCTAssertTrue(c.aborts)
    }

    // G18 zero-byte burst
    func testG18ZeroByteStagingIsIncomplete() {
        let p = StagingPolicy(expectedFileCount: 1, expectedTotalBytes: 1, expectedContentMultisetSHA256: "x")
        let s = StagingSnapshot(observedAt: 10, files: [StagingFileRecord(name: "a.jpg", size: 0, modificationTime: 0, sha256: "a", decodable: false)])
        XCTAssertEqual(StagingVerifier.verify(snapshot: s, policy: p).outcome, .stagingIncomplete)
    }

    // G19 partial download
    func testG19PartialSuffixIsIncomplete() {
        let p = StagingPolicy(expectedFileCount: 1, expectedTotalBytes: 1, expectedContentMultisetSHA256: "x")
        let s = StagingSnapshot(observedAt: 10, files: [StagingFileRecord(name: "a.jpg.partial", size: 1, modificationTime: 0, sha256: "a", decodable: true)])
        XCTAssertEqual(StagingVerifier.verify(snapshot: s, policy: p).outcome, .stagingIncomplete)
    }

    // G20 duplicate files / 58th file
    func testG20ExtraFileHasDedicatedOutcome() {
        let p = StagingPolicy(expectedFileCount: 1, expectedTotalBytes: 1, expectedContentMultisetSHA256: "x")
        let files = [
            StagingFileRecord(name: "a.jpg", size: 1, modificationTime: 0, sha256: "a", decodable: true),
            StagingFileRecord(name: "b.jpg", size: 1, modificationTime: 0, sha256: "b", decodable: true),
        ]
        XCTAssertEqual(StagingVerifier.verify(snapshot: StagingSnapshot(observedAt: 10, files: files), policy: p).outcome, .stagingExtraFiles)
    }

    // G21 restart observe-only
    func testG21RestartAfterSaveAllCannotRedispatch() throws {
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        let ledger = try IntentLedger(fileURL: dir.appendingPathComponent("ledger.jsonl"))
        try ledger.append(kind: "dispatch.saveAll")
        XCTAssertTrue(LedgerResume.wouldRefuseNewIrreversibleDispatch(entries: ledger.entries))
    }

    // G22 multi-display / wrong scale
    func testG22IndependentScaleMismatchFailsClosed() {
        XCTAssertEqual(
            CaptureGeometryRules.validateScale(pointPixelScale: 1, backingScaleFactor: 2),
            .scaleMismatch(pointPixelScale: 1, backingScaleFactor: 2)
        )
    }

    // X01 stale AX after relayout
    func testX01RelayoutFrameDeltaInvalidatesRead() {
        let relaid = fresh(frame: CGRect(x: 10, y: 20, width: 500, height: 643))
        XCTAssertFalse(WindowIdentityValidator.isFresh(identity: identity(), against: relaid, maxFrameDeltaPt: 1, currentEpoch: 1))
    }

    // X02 popup-inside-main vs separate popup surface
    func testX02MenuWithoutAddressablePopupOverlapRefuses() {
        guard case let .refused(reason, _) = StructuralLocators.locateSaveAll(
            rows: rows(),
            menuBounds: CGRect(x: 20, y: 10, width: 220, height: 270),
            addressableBounds: CGRect(x: 900, y: 900, width: 20, height: 20),
            binding: binding
        ) else { return XCTFail("must refuse") }
        XCTAssertEqual(reason, .unsafeGeometry)
    }

    // X03 target inactive when event would post
    func testX03InactiveTargetFailsFinalDispatchGate() {
        let readiness = DispatchReadiness(applicationActive: true, targetFrontmost: false, identityFresh: true, candidateFresh: true, geometrySafe: true)
        XCTAssertFalse(DispatchReadinessEvaluator.isEligible(readiness))
        XCTAssertEqual(DispatchReadinessEvaluator.refusal(for: readiness), .targetNotFrontmost)
    }
}
