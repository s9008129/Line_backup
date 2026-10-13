import CoreGraphics
import Foundation

/// Pure, diagnostic-only facts. Candidate children are not parentage or occlusion proof.
public struct ExplicitLineDisplaySnapshot: Equatable, Codable, Sendable {
    public var displayID: UInt32
    public var frame: CGRect
    public var widthPt: Int
    public var heightPt: Int

    public init(displayID: UInt32, frame: CGRect, widthPt: Int, heightPt: Int) {
        self.displayID = displayID; self.frame = frame; self.widthPt = widthPt; self.heightPt = heightPt
    }
}

/// Original request retained independently of the source's effective configuration.
/// The rulebook is the already retained frozen geometry input, not new calibration.
public struct ExplicitLineRequestBinding: Equatable, Codable, Sendable {
    public var configuration: CaptureConfiguration
    public var geometryState: CaptureGeometryState
    public var settledSelectedWindows: [SCWindowSnapshot]
    public var ruleBook: CaptureGeometryRuleBook

    public init(configuration: CaptureConfiguration, geometryState: CaptureGeometryState,
                settledSelectedWindows: [SCWindowSnapshot], ruleBook: CaptureGeometryRuleBook) {
        self.configuration = configuration; self.geometryState = geometryState
        self.settledSelectedWindows = settledSelectedWindows; self.ruleBook = ruleBook
    }
}

public struct ExplicitLineSelectionWitness: Equatable, Codable, Sendable {
    public var filterKind: String
    public var selectedWindowIDs: [UInt32]
    public var display: ExplicitLineDisplaySnapshot
    public var effectiveSourceRect: CGRect
    public var filterContentRect: CGRect
    public var pointPixelScale: Double
    public var includeChildWindows: Bool
    public var includeMenuBar: Bool

    public init(filterKind: String = "displayIncludingExactWindows", selectedWindowIDs: [UInt32],
                display: ExplicitLineDisplaySnapshot, effectiveSourceRect: CGRect, filterContentRect: CGRect,
                pointPixelScale: Double, includeChildWindows: Bool = false, includeMenuBar: Bool = false) {
        self.filterKind = filterKind; self.selectedWindowIDs = selectedWindowIDs; self.display = display
        self.effectiveSourceRect = effectiveSourceRect; self.filterContentRect = filterContentRect
        self.pointPixelScale = pointPixelScale; self.includeChildWindows = includeChildWindows; self.includeMenuBar = includeMenuBar
    }
}

public enum ExplicitLineCaptureSelection {
    public static let rulePrefix = "explicitLineWindows-v3-"
    public static func normalized(_ windows: [SCWindowSnapshot]) -> [SCWindowSnapshot] {
        windows.sorted { $0.windowID < $1.windowID }
    }
    public static func validRect(_ rect: CGRect) -> Bool {
        [rect.origin.x, rect.origin.y, rect.width, rect.height].allSatisfy(\.isFinite)
            && rect.width > 0 && rect.height > 0
    }
    private static func refuse(_ detail: String) -> ObservationRefusal {
        .invalidBundle("explicitLineWindows: " + detail)
    }
    public static func selectedWindows(in inventory: [SCWindowSnapshot], target: ObservationTarget) throws -> [SCWindowSnapshot] {
        guard target.bundleID == ObservationTarget.lineBundleID, target.pid > 0 else { throw refuse("fixed LINE target required") }
        let mains = WindowSensor.mainWindowCandidates(in: inventory, bundleID: target.bundleID, pid: target.pid)
        guard mains.count == 1, let main = mains.first, validRect(main.frame) else { throw refuse("unique valid main required") }
        let children = WindowSensor.childWindows(of: main, in: inventory)
        let selected = [main] + children
        guard !children.isEmpty, Set(selected.map(\.windowID)).count == selected.count,
              selected.allSatisfy({ window in window.windowID > 0 && validRect(window.frame)
                  && window.ownerPID == target.pid && window.ownerBundleID == target.bundleID && window.isOnScreen
                  && inventory.filter({ $0.windowID == window.windowID }).count == 1 }) else {
            throw refuse("affirmative unique LINE candidate children required")
        }
        return normalized(selected)
    }
    public static func union(of windows: [SCWindowSnapshot]) throws -> CGRect {
        guard let first = windows.first, windows.allSatisfy({ validRect($0.frame) }) else { throw refuse("invalid selected bounds") }
        let bounds = windows.dropFirst().reduce(first.frame) { $0.union($1.frame) }
        guard validRect(bounds) else { throw refuse("invalid union") }
        return bounds
    }
    /// Fresh enumeration must resolve the entire requested set, including frame/owner/layer facts.
    public static func validateFreshSelection(requested: [SCWindowSnapshot], inventory: [SCWindowSnapshot],
                                              target: ObservationTarget, main: SCWindowSnapshot) throws {
        let selected = try selectedWindows(in: inventory, target: target)
        guard normalized(requested) == selected, selected.filter({ $0.windowID == main.windowID }) == [main], main.windowLayer == 0 else {
            throw refuse("native handles no longer match requested exact selection")
        }
    }
    public static func containingDisplay(for bounds: CGRect, displays: [ExplicitLineDisplaySnapshot]) throws -> ExplicitLineDisplaySnapshot {
        guard validRect(bounds), !displays.isEmpty,
              Set(displays.map(\.displayID)).count == displays.count,
              displays.allSatisfy({ $0.displayID > 0 && validRect($0.frame) && $0.widthPt > 0 && $0.heightPt > 0
                  && $0.frame.width == CGFloat($0.widthPt) && $0.frame.height == CGFloat($0.heightPt) }) else { throw refuse("invalid display inventory") }
        let intersecting = displays.filter { $0.frame.intersects(bounds) }
        guard intersecting.count == 1, let display = intersecting.first,
              display.frame.origin == .zero, display.frame.contains(bounds) else {
            throw refuse("requires one zero-origin display containing the complete union")
        }
        return display
    }
    public static func validateRuleBook(_ ruleBook: CaptureGeometryRuleBook, state: CaptureGeometryState) throws {
        guard ruleBook.ruleID.hasPrefix(rulePrefix), !ruleBook.frozenAtISO8601.isEmpty,
              state.settled, !state.includeChildWindows, state.ignoreShadows,
              let rule = ruleBook.rule(for: state),
              [rule.maxPerSideSizeDeltaPt, rule.originPaddingPt, rule.maxOriginPaddingPt].allSatisfy(\.isFinite),
              rule.maxPerSideSizeDeltaPt >= 0, rule.maxPerSideSizeDeltaPt <= 1,
              rule.maxOriginPaddingPt >= 0, rule.maxOriginPaddingPt <= 1,
              rule.originPaddingPt >= 0, rule.originPaddingPt <= rule.maxOriginPaddingPt else { throw refuse("profile-specific frozen rule required; no relaxed tolerance") }
    }
    public static func validateRequest(_ binding: ExplicitLineRequestBinding, configuration: CaptureConfiguration,
                                       state: CaptureGeometryState, target: ObservationTarget,
                                       preInventory: [SCWindowSnapshot]) throws {
        guard configuration == .explicitLineWindows, binding.configuration == configuration,
              binding.geometryState == state else { throw refuse("original request/configuration/state mismatch") }
        try validateRuleBook(binding.ruleBook, state: state)
        let selected = try selectedWindows(in: preInventory, target: target)
        guard binding.settledSelectedWindows == selected else { throw refuse("settling selection changed before session capture") }
    }
    /// The single validator called before session success/count and by retained reconstruction.
    public static func validate(binding: ExplicitLineRequestBinding?, target: ObservationTarget, mainID: UInt32,
                                preInventory: [SCWindowSnapshot], postInventory: [SCWindowSnapshot], frame: CapturedFrameRecord) throws {
        guard let binding, let witness = frame.explicitLineSelectionWitness else { throw refuse("missing original binding or selection witness") }
        try validateRequest(binding, configuration: binding.configuration, state: binding.geometryState, target: target, preInventory: preInventory)
        let pre = try selectedWindows(in: preInventory, target: target)
        let post = try selectedWindows(in: postInventory, target: target)
        let bounds = try union(of: pre)
        var effective = binding.configuration
        effective.sourceRect = bounds
        let display = try containingDisplay(for: bounds, displays: [witness.display])
        guard pre == post, normalized(frame.includedWindows) == pre,
              pre.filter({ $0.windowID == mainID && $0.windowLayer == 0 }).count == 1,
              frame.captureKind == .explicitLineWindows, frame.configuration == effective,
              frame.expectedBBoxPt == bounds, frame.stateKey == CaptureGeometryRules.stateKey(binding.geometryState),
              witness.filterKind == "displayIncludingExactWindows", witness.selectedWindowIDs == pre.map(\.windowID),
              witness.effectiveSourceRect == bounds, !witness.includeChildWindows, !witness.includeMenuBar,
              validRect(witness.filterContentRect), display.frame.contains(witness.filterContentRect), witness.filterContentRect.contains(bounds),
              witness.pointPixelScale.isFinite, witness.pointPixelScale > 0, witness.pointPixelScale == frame.scale,
              frame.scale.isFinite, frame.scale > 0, frame.backingScaleFactor.isFinite, frame.backingScaleFactor > 0,
              frame.scaleSource == .pointPixelScale,
              CaptureGeometryRules.validateScale(pointPixelScale: frame.scale, backingScaleFactor: frame.backingScaleFactor) == nil,
              frame.validity == .valid, frame.violations.isEmpty else { throw refuse("selected set/effective configuration/witness/scale mismatch") }
        let evaluation = try CaptureGeometryRules.evaluate(expectedBBox: bounds, imageWidthPx: frame.imageWidthPx,
            imageHeightPx: frame.imageHeightPx, scale: frame.scale, ruleBook: binding.ruleBook, state: binding.geometryState).get()
        guard evaluation.actualBBoxPt == frame.actualBBoxPt, evaluation.perSideSizeDeltaPt == frame.perSideSizeDeltaPt,
              evaluation.stateKey == frame.stateKey else { throw refuse("recorded geometry does not recompute") }
    }
}
