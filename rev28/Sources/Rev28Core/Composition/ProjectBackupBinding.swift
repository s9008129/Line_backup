import Foundation
import CoreFoundation
import CryptoKit

public struct ProjectBackupInspectionRequest: Equatable, Sendable {
    public let projectRoot: String
    public let startDate: String
    public let endDate: String
    public let expectedImages: Int
    public init(projectRoot: String, startDate: String, endDate: String, expectedImages: Int) {
        self.projectRoot = projectRoot; self.startDate = startDate
        self.endDate = endDate; self.expectedImages = expectedImages
    }
}

public struct ProjectBackupProducerSourceMaterial: Sendable {
    public let relativePath: String
    public let rawBytes: Data
    public init(relativePath: String, rawBytes: Data) {
        self.relativePath = relativePath; self.rawBytes = rawBytes
    }
}

public enum ProjectBackupInspectionDecision: String, Sendable {
    case eligible = "PROJECT_TARGET_ELIGIBLE_FOR_INSPECTION"
    case skipVerified = "SKIP_VERIFIED"
    case busy = "PROJECT_BUSY"
    case unresolved = "BLOCKED_UNRESOLVED"
    case ambiguous = "AMBIGUOUS_FINGERPRINT"
    case destinationBlocked = "BLOCKED_DESTINATION"
}

/// A value for inspection only. It cannot construct any native permit or acquire ownership.
public struct ProjectBackupInspectionBinding: Sendable {
    public var canDispatch: Bool { false }
    public let request: ProjectBackupInspectionRequest
    public let decision: ProjectBackupInspectionDecision
    public let groupKey: String
    public let proposedDestination: String
    public let stateRevision: Int
    public let stdoutSHA256: String
    fileprivate init(request: ProjectBackupInspectionRequest, decision: ProjectBackupInspectionDecision,
                     groupKey: String, proposedDestination: String, stateRevision: Int, stdoutSHA256: String) {
        self.request = request; self.decision = decision; self.groupKey = groupKey
        self.proposedDestination = proposedDestination; self.stateRevision = stateRevision
        self.stdoutSHA256 = stdoutSHA256
    }
}

public enum ProjectBackupBindingError: Error, Equatable {
    case invalidJSON, invalidContract, inconsistentAuthority, inconsistentHistory, inconsistentSource
}

/// Pure byte consumer. External anchors bind supplied material, not OS code attestation or freshness.
public enum ProjectBackupBinding {
    private typealias Object = [String: Any]
    private static let sourceNames = ["__init__.py", "__main__.py", "authority.py", "cli.py", "common.py",
                                      "manual_archive.py", "project_binding.py", "status.py", "transaction.py", "verifier.py"]
    private static let phases = Set(["LOAD_STATE", "CUA_RUNTIME_GATE", "TARGET_CONTEXT", "TARGET_CONTEXT_LOCKED", "ALBUM_DISCOVERY", "DUPLICATE_GATE", "PREPARE_DESTINATION", "OPEN_ALBUM", "SAVE_ALL_CALIBRATION", "SAVE_ALL_INTENT_COMMITTED", "SAVE_ALL_TRIGGERED", "CHOOSER", "DOWNLOAD_STARTED", "VERIFYING", "VERIFIED", "SAFE_ABORT", "ABORTED_BEFORE_SAVE_ALL_DISPATCH", "SAVE_ALL_DISPATCH_ATTEMPTED", "TRIGGER_CONFIRMED", "TRIGGER_UNKNOWN", "NONDESTRUCTIVE_CALIBRATION_MODE"])
    private static func require(_ condition: Bool, _ error: ProjectBackupBindingError = .invalidContract) throws {
        if !condition { throw error }
    }
    private static func hash(_ data: Data) -> String {
        SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
    }
    private static func object(_ value: Any?, keys: [String]? = nil) throws -> Object {
        guard let o = value as? Object else { throw ProjectBackupBindingError.invalidContract }
        if let keys { try require(Set(o.keys) == Set(keys)) }
        return o
    }
    private static func array(_ value: Any?) throws -> [Any] {
        guard let a = value as? [Any] else { throw ProjectBackupBindingError.invalidContract }; return a
    }
    private static func string(_ value: Any?) throws -> String {
        guard let s = value as? String, !s.isEmpty else { throw ProjectBackupBindingError.invalidContract }; return s
    }
    private static func int(_ value: Any?, minimum: Int = 0) throws -> Int {
        guard let n = value as? NSNumber, CFGetTypeID(n) != CFBooleanGetTypeID(),
              String(cString: n.objCType) != "d", String(cString: n.objCType) != "f",
              n.int64Value >= Int64(minimum), n.int64Value <= 9_007_199_254_740_991 else {
            throw ProjectBackupBindingError.invalidContract
        }
        return n.intValue
    }
    private static func bool(_ value: Any?) throws -> Bool {
        guard let n = value as? NSNumber, CFGetTypeID(n) == CFBooleanGetTypeID() else {
            throw ProjectBackupBindingError.invalidContract
        }; return n.boolValue
    }
    private static func isNull(_ value: Any?) -> Bool { value is NSNull }
    private static func equal(_ a: Any, _ b: Any) -> Bool { (a as AnyObject).isEqual(b) }
    private static func optionalString(_ value: Any?) throws -> String? {
        if isNull(value) { return nil }; return try string(value)
    }
    private static func strings(_ value: Any?) throws -> [String] {
        let result = try array(value).map { try string($0) }
        try require(Set(result).count == result.count); return result
    }
    private static func component(_ s: String) -> Bool {
        !s.isEmpty && s != "." && s != ".." && !s.contains("/") && !s.contains("\\") &&
            !s.unicodeScalars.contains { $0.value < 32 }
    }
    private static func path(_ s: String) -> Bool {
        s.hasPrefix("/") && s != "/" && s.dropFirst().split(separator: "/", omittingEmptySubsequences: false).allSatisfy { component(String($0)) }
    }
    private static func validDate(_ s: String) -> Bool {
        guard s.utf8.count == 10, s.range(of: "^[0-9]{4}-[0-9]{2}-[0-9]{2}$", options: .regularExpression) != nil else { return false }
        let p = s.split(separator: "-").compactMap { Int($0) }
        guard p.count == 3, p[0] > 0, (1...12).contains(p[1]) else { return false }
        let leap = p[0] % 4 == 0 && (p[0] % 100 != 0 || p[0] % 400 == 0)
        let days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        return (1...days[p[1] - 1]).contains(p[2])
    }
    private static func fingerprint(_ value: Any?) throws -> Object {
        let o = try object(value, keys: ["start_date", "end_date", "expected_images"])
        let start = try string(o["start_date"]), end = try string(o["end_date"])
        try require(validDate(start) && validDate(end) && start <= end)
        _ = try int(o["expected_images"], minimum: 1); return o
    }
    private static func digest(_ value: Any?, path: String, bytes: Data) throws {
        let o = try object(value, keys: ["path", "bytes", "sha256"])
        try require(try string(o["path"]) == path && int(o["bytes"]) == bytes.count && string(o["sha256"]) == hash(bytes), .inconsistentAuthority)
    }
    private static func json(_ data: Data) throws -> Object {
        guard data.count <= 16 * 1024 * 1024, String(data: data, encoding: .utf8) != nil else { throw ProjectBackupBindingError.invalidJSON }
        var scanner = DuplicateKeyScanner(bytes: Array(data)); try scanner.scan()
        do { return try object(JSONSerialization.jsonObject(with: data)) }
        catch { throw ProjectBackupBindingError.invalidJSON }
    }
    private static func config(_ c: Object, root: String) throws {
        try require(Set(c.keys) == Set(["schema_version", "group_key", "group_name", "backup_root", "app_identifier", "max_albums_per_run", "recovery_limit", "poll_interval_seconds", "stable_samples", "max_wait_seconds"]))
        let name = try string(c["group_name"])
        try require(component(name) && path(root), .inconsistentAuthority)
        try require(try int(c["schema_version"]) == 2 && string(c["app_identifier"]) == "jp.naver.line.mac" &&
                    string(c["group_key"]) == "line:jp.naver.line.mac:" + name && string(c["backup_root"]) == root + "/backups", .inconsistentAuthority)
        for key in ["max_albums_per_run", "recovery_limit", "poll_interval_seconds", "stable_samples", "max_wait_seconds"] { _ = try int(c[key], minimum: 1) }
        try require(try int(c["recovery_limit"]) == 1)
    }
    private static func terminal(_ r: Object) -> Bool { ["VERIFIED", "SAFE_ABORT"].contains(r["workflow_outcome"] as? String ?? "") }
    private static func unresolved(_ r: Object) throws -> Bool {
        if r["workflow_outcome"] as? String == "VERIFIED" { return false }
        return try !terminal(r) || !isNull(r["intent"]) || !["NONE", "INTENT_NONE"].contains(string(r["intent_state"])) || bool(r["manual_reconciliation_required"]) ||
            !["NOT_ATTEMPTED", "ELLIPSIS_FAILED"].contains(r["dispatch_state"] as? String ?? "NOT_ATTEMPTED") || !(r["reconciliations"] as? [Any] ?? []).isEmpty
    }
    private static func checkpoint(_ value: Any?) throws {
        let c = try object(value, keys: ["phase", "at", "evidence"])
        try require(try phases.contains(string(c["phase"])))
        try require(c["at"] is String && c["evidence"] is String)
    }
    private static func dispatchEvidence(_ value: Any?) throws {
        let d = try object(value, keys: ["run_id", "action_id", "execution_id", "observed_at", "save_all_click_count", "save_all_invocation_attempted", "failure_boundary", "folder_chooser_appeared", "download_started", "provenance"])
        for k in ["run_id", "action_id", "execution_id", "observed_at", "provenance"] { _ = try string(d[k]) }
        if !isNull(d["save_all_click_count"]) { try require(try int(d["save_all_click_count"]) <= 1) }
        for k in ["save_all_invocation_attempted", "folder_chooser_appeared", "download_started"] { if !isNull(d[k]) { _ = try bool(d[k]) } }
        try require(try ["ELLIPSIS_CLICK", "BEFORE_SAVE_ALL_INVOCATION", "SAVE_ALL_INVOCATION", "AFTER_SAVE_ALL_INVOCATION", "NONE", "UNKNOWN"].contains(string(d["failure_boundary"])))
    }
    private static func state(_ s: Object, group: String, backup: String) throws -> ([Object], [Object]) {
        let version = try int(s["schema_version"])
        try require([2, 3].contains(version))
        var keys = Set(["schema_version", "revision", "current_run_id", "verified_albums", "runs", "active_writer_id", "context_lock"])
        if version == 3 { keys.insert("active_batch") }
        try require(Set(s.keys) == keys); _ = try int(s["revision"])
        if version == 3 && !isNull(s["active_batch"]) {
            let b = try object(s["active_batch"], keys: ["batch_id", "owner_execution_id", "group_key", "mode", "phase", "policy_version", "config_sha256", "source_sha256", "created_at", "authorized_new_download_limit", "configured_new_download_limit", "new_transactions_reserved", "manifest_reference", "next_index", "current_album_run_id", "stop_reason"])
            try require(try string(b["group_key"]) == group && string(b["policy_version"]) == "batch-policy-1")
            for k in ["batch_id", "owner_execution_id", "created_at"] { _ = try string(b[k]) }
            for k in ["config_sha256", "source_sha256"] { try require(try string(b[k]).range(of: "^[0-9a-f]{64}$", options: .regularExpression) != nil) }
            let limit = try int(b["authorized_new_download_limit"]), configured = try int(b["configured_new_download_limit"], minimum: 1)
            let reserved = try int(b["new_transactions_reserved"]); _ = try int(b["next_index"])
            try require(reserved <= min(limit, configured))
            let mode = try string(b["mode"]), phase = try string(b["phase"])
            try require(["catalog_only", "backup_batch"].contains(mode) && ["CATALOG", "ADMITTED", "RUNNING", "STOPPED", "COMPLETED"].contains(phase))
            let album = try optionalString(b["current_album_run_id"]); _ = try optionalString(b["stop_reason"])
            if mode == "catalog_only" { try require(limit == 0 && reserved == 0 && album == nil) }
            if ["ADMITTED", "RUNNING"].contains(phase) { try require(!isNull(b["manifest_reference"])) }
            if !isNull(b["manifest_reference"]) {
                let m = try object(b["manifest_reference"], keys: ["path", "bytes", "sha256"])
                let p = try string(m["path"]); try require(p.hasPrefix("harness-development/") && p.split(separator: "/", omittingEmptySubsequences: false).allSatisfy { component(String($0)) })
                _ = try int(m["bytes"], minimum: 1); try require(try string(m["sha256"]).range(of: "^[0-9a-f]{64}$", options: .regularExpression) != nil)
            }
            if album == nil { try require(isNull(s["active_writer_id"]) && isNull(s["context_lock"])) }
            else { try require(try optionalString(s["current_run_id"]) == album && optionalString(s["active_writer_id"]) == string(b["owner_execution_id"])) }
        } else if version == 3 { try require(isNull(s["active_writer_id"]) && isNull(s["context_lock"])) }
        let current = try optionalString(s["current_run_id"]); _ = try optionalString(s["active_writer_id"])
        if !isNull(s["context_lock"]) {
            let lock = try object(s["context_lock"], keys: ["group_key", "source", "confirmed_at", "execution_id", "continuity_evidence"])
            try require(try string(lock["group_key"]) == group && ["USER_CONFIRMATION", "RELIABLE_VISUAL_NAVIGATION"].contains(string(lock["source"])), .inconsistentHistory)
            for k in ["confirmed_at", "execution_id", "continuity_evidence"] { _ = try string(lock[k]) }
        }
        let runs = try array(s["runs"]).map { try object($0) }
        let entries = try array(s["verified_albums"]).map { try object($0, keys: ["group_key", "fingerprint", "verified_run_id", "destinations", "source_kind", "evidence"]) }
        let required: Set<String> = ["run_id", "mode", "group_key", "album_id", "fingerprint", "observed_title", "title_confidence", "destination", "destination_initially_empty", "phase", "checkpoint", "events", "intent", "recovery_used", "runtime_errors", "verification", "workflow_outcome", "stop_reason", "batch_id", "intent_state", "manual_reconciliation_required", "reconciliation_reason"]
        var ids = Set<String>()
        func destination(_ value: Any?) throws {
            if let d = try optionalString(value) { try require(path(d) && d.hasPrefix(backup + "/"), .inconsistentHistory) }
        }
        for r in runs {
            let rid = try string(r["run_id"]); try require(ids.insert(rid).inserted, .inconsistentHistory)
            let keys = Set(r.keys), rc2 = r["contract_revision"] != nil
            let extra: Set<String> = rc2 ? ["contract_revision", "dispatch_state", "dispatch_evidence", "reconciliations"] : ["reconciliations"]
            try require(required.isSubset(of: keys) && keys.isSubset(of: required.union(extra)))
            try require(try string(r["group_key"]) == group, .inconsistentHistory)
            try require(try ["IN_PROGRESS", "VERIFIED", "FAILED", "SAFE_ABORT"].contains(string(r["workflow_outcome"])))
            try require(try ["backup_one", "backup_batch", "resume"].contains(string(r["mode"])))
            try require(try ["HIGH", "LOW", "UNKNOWN"].contains(string(r["title_confidence"])))
            _ = try bool(r["destination_initially_empty"]); _ = try bool(r["manual_reconciliation_required"])
            if !isNull(r["fingerprint"]) { _ = try fingerprint(r["fingerprint"]) }
            try destination(r["destination"])
            let intentStates = rc2 ? ["INTENT_NONE", "INTENT_COMMITTED", "ABORTED_BEFORE_SAVE_ALL_DISPATCH", "SAVE_ALL_DISPATCH_ATTEMPTED", "TRIGGER_CONFIRMED", "TRIGGER_UNKNOWN"] : ["NONE", "COMMITTED_NOT_DISPATCHED", "DISPATCHED", "TRIGGER_CONFIRMED", "UNKNOWN"]
            try require(try intentStates.contains(string(r["intent_state"])))
            if rc2 {
                try require(r["contract_revision"] as? String == "1.0-rc2")
                try require(try ["NOT_ATTEMPTED", "ELLIPSIS_FAILED", "SAVE_ALL_ATTEMPTED", "SAVE_ALL_RETURNED", "UNKNOWN"].contains(string(r["dispatch_state"])))
                _ = try array(r["reconciliations"])
                if !isNull(r["dispatch_evidence"]) { try dispatchEvidence(r["dispatch_evidence"]) }
            }
            try require(try phases.contains(string(r["phase"])))
            try checkpoint(r["checkpoint"])
            for event in try array(r["events"]) { try checkpoint(event) }
            _ = try object(r["recovery_used"]); _ = try array(r["runtime_errors"])
            if try bool(r["manual_reconciliation_required"]) { _ = try string(r["reconciliation_reason"]) }
            if !isNull(r["intent"]) {
                let i = try object(r["intent"], keys: ["action_id", "committed_at", "owner_execution_id", "group_key", "fingerprint", "destination", "calibration", "save_all_retry_allowed", "dispatch_outcome", "trigger_outcome"])
                try require(try string(i["group_key"]) == group && equal(i["fingerprint"]!, r["fingerprint"]!) && equal(i["destination"]!, r["destination"]!), .inconsistentHistory)
                _ = try fingerprint(i["fingerprint"]); try require(try bool(i["save_all_retry_allowed"]) == false)
                for k in ["action_id", "committed_at", "owner_execution_id"] { _ = try string(i[k]) }
                try require(try ["NOT_ATTEMPTED", "RETURNED", "ERROR", "UNKNOWN"].contains(string(i["dispatch_outcome"])))
                try require(try ["NOT_OBSERVED", "CHOOSER_CONFIRMED", "UNKNOWN", "UNEXPECTED_UI", "NOT_APPLICABLE", "NOT_TRIGGERED", "TRIGGER_CONFIRMED"].contains(string(i["trigger_outcome"])))
                let cal = try object(i["calibration"], keys: ["observed_at", "screenshot_width", "screenshot_height", "ellipsis", "dot_spacing", "save_all_point", "confidence", "evidence"])
                _ = try int(cal["screenshot_width"], minimum: 1); _ = try int(cal["screenshot_height"], minimum: 1)
                try require(cal["confidence"] as? String == "HIGH"); _ = try string(cal["evidence"])
                guard cal["observed_at"] is String else { throw ProjectBackupBindingError.invalidContract }
            }
            let reconciliations = r["reconciliations"] == nil ? [] : try array(r["reconciliations"])
            for rec in reconciliations {
                let o = try object(rec, keys: ["reconciliation_id", "recorded_at", "run_id", "action_id", "execution_id", "outcome", "trigger_outcome", "blocking_intent_released", "manual_reconciliation_required", "original_observation", "proof", "evidence"])
                _ = try bool(o["blocking_intent_released"]); _ = try bool(o["manual_reconciliation_required"])
                for k in ["reconciliation_id", "recorded_at", "run_id", "action_id", "execution_id", "evidence"] { _ = try string(o[k]) }
                try require(try ["ABORTED_BEFORE_SAVE_ALL_DISPATCH", "EVIDENCE_RECONCILED"].contains(string(o["outcome"])))
                try require(try ["NOT_TRIGGERED", "TRIGGER_CONFIRMED", "UNKNOWN"].contains(string(o["trigger_outcome"])))
                let obs = try object(o["original_observation"], keys: ["reference", "trigger_outcome"]); _ = try string(obs["reference"])
                try require(try ["NOT_OBSERVED", "CHOOSER_CONFIRMED", "UNKNOWN", "UNEXPECTED_UI", "NOT_APPLICABLE", "NOT_TRIGGERED", "TRIGGER_CONFIRMED"].contains(string(obs["trigger_outcome"])))
                if !isNull(o["proof"]) { try dispatchEvidence(o["proof"]) }
                if o["outcome"] as? String == "ABORTED_BEFORE_SAVE_ALL_DISPATCH" {
                    let proof = try object(o["proof"])
                    try require(try int(proof["save_all_click_count"]) == 0 && !bool(proof["save_all_invocation_attempted"]) && !bool(proof["folder_chooser_appeared"]) && !bool(proof["download_started"]) && ["ELLIPSIS_CLICK", "BEFORE_SAVE_ALL_INVOCATION"].contains(string(proof["failure_boundary"])))
                    try require(try bool(o["blocking_intent_released"]) && !bool(o["manual_reconciliation_required"]) && string(o["trigger_outcome"]) == "NOT_TRIGGERED")
                }
            }
            if rc2 && r["intent_state"] as? String == "ABORTED_BEFORE_SAVE_ALL_DISPATCH" {
                try require(r["workflow_outcome"] as? String == "SAFE_ABORT" && reconciliations.contains { ($0 as? Object)?["outcome"] as? String == "ABORTED_BEFORE_SAVE_ALL_DISPATCH" })
            }
            if !isNull(r["verification"]) {
                let v = try object(r["verification"], keys: ["observed_at", "outcome", "regular_files", "image_files", "subdirectories", "total_bytes", "extensions", "metadata_files", "zero_byte_files", "partial_temp_files", "unrecognized_files", "other_entries", "stable_samples", "inventory", "evidence"])
                _ = try array(v["inventory"])
                try require(try ["PASS", "FAIL", "INCOMPLETE_OR_STILL_DOWNLOADING"].contains(string(v["outcome"])))
            }
            if r["workflow_outcome"] as? String == "VERIFIED" {
                let f = try fingerprint(r["fingerprint"]), v = try object(r["verification"])
                try require(!isNull(r["destination"]) && v["outcome"] as? String == "PASS", .inconsistentHistory)
                try require(try int(v["image_files"], minimum: 1) == int(f["expected_images"], minimum: 1), .inconsistentHistory)
                _ = try string(v["evidence"])
            }
        }
        if let current { try require(ids.contains(current), .inconsistentHistory) }
        for e in entries {
            try require(try string(e["group_key"]) == group, .inconsistentHistory)
            _ = try fingerprint(e["fingerprint"])
            let destinations = try strings(e["destinations"]); try require(!destinations.isEmpty)
            for d in destinations { try destination(d) }
            let rid = try optionalString(e["verified_run_id"])
            if e["source_kind"] as? String == "filesystem_verification" {
                guard let r = runs.first(where: { $0["run_id"] as? String == rid }) else { throw ProjectBackupBindingError.inconsistentHistory }
                try require(r["workflow_outcome"] as? String == "VERIFIED" && equal(r["fingerprint"]!, e["fingerprint"]!) && destinations.contains(r["destination"] as? String ?? ""), .inconsistentHistory)
            } else { try require(e["source_kind"] as? String == "user_attestation" && rid == nil, .inconsistentHistory) }
            let evidence = try string(e["evidence"])
            let parts = evidence.split(separator: ":", omittingEmptySubsequences: false)
            try require(parts.count == 3 && ["join", "user_fact", "fixture"].contains(String(parts[0])) &&
                        parts[1].split(separator: "/", omittingEmptySubsequences: false).allSatisfy { component(String($0)) } && !parts[1].hasPrefix("/") &&
                        parts[2].range(of: "^[0-9a-f]{64}$", options: .regularExpression) != nil, .inconsistentHistory)
        }
        return (runs, entries)
    }

    public static func inspect(originalRequest: ProjectBackupInspectionRequest, rawConfig: Data, rawState: Data,
                               producerStdout: Data, externalStdoutSHA256: String,
                               producerSourceMaterial: [ProjectBackupProducerSourceMaterial]) throws -> ProjectBackupInspectionBinding {
        try require(hash(producerStdout) == externalStdoutSHA256, .inconsistentAuthority)
        let report = try json(producerStdout), c = try json(rawConfig), s = try json(rawState)
        try require(Set(report.keys) == Set(["report_format_version", "kind", "scope", "request", "authority", "target", "decision", "reasons", "state_facts", "producer", "expected_total_bytes", "expected_content_multiset_sha256", "content_expectation", "dispatch_authorized", "writer_acquired", "native_observation_performed", "state_modified"]))
        try require(try int(report["report_format_version"]) == 1 && string(report["kind"]) == "REPORT" && string(report["scope"]) == "PROJECT_PREFLIGHT_READ_ONLY")
        for k in ["dispatch_authorized", "writer_acquired", "native_observation_performed", "state_modified"] { try require(try bool(report[k]) == false) }
        try require(isNull(report["expected_total_bytes"]) && isNull(report["expected_content_multiset_sha256"]) && report["content_expectation"] as? String == "MEASURE_AFTER_DOWNLOAD_NOT_YET_VERIFIED")
        let reasons = try array(report["reasons"]).map { try string($0) }; try require(!reasons.isEmpty)
        try config(c, root: originalRequest.projectRoot)
        try require(validDate(originalRequest.startDate) && validDate(originalRequest.endDate) && originalRequest.startDate <= originalRequest.endDate && originalRequest.expectedImages > 0 && originalRequest.expectedImages <= 9_007_199_254_740_991)
        let request = try object(report["request"], keys: ["project_root", "start_date", "end_date", "expected_images"])
        try require(try string(request["project_root"]) == originalRequest.projectRoot && string(request["start_date"]) == originalRequest.startDate && string(request["end_date"]) == originalRequest.endDate && int(request["expected_images"], minimum: 1) == originalRequest.expectedImages, .inconsistentAuthority)
        let authority = try object(report["authority"], keys: ["project_root", "config", "state", "state_revision", "group_name", "group_key", "app_identifier", "backup_root"])
        try digest(authority["config"], path: "config/line_backup_config.json", bytes: rawConfig)
        try digest(authority["state"], path: "state/backup_state.json", bytes: rawState)
        try require(try int(authority["state_revision"]) == int(s["revision"]) && string(authority["project_root"]) == originalRequest.projectRoot, .inconsistentAuthority)
        for k in ["group_name", "group_key", "app_identifier", "backup_root"] { try require(equal(authority[k]!, c[k]!), .inconsistentAuthority) }
        let group = try string(c["group_key"]), backup = try string(c["backup_root"])
        let (runs, entries) = try state(s, group: group, backup: backup)
        let target = try object(report["target"], keys: ["group_key", "fingerprint", "proposed_destination"])
        let f = try fingerprint(target["fingerprint"])
        let expected: Object = ["start_date": originalRequest.startDate, "end_date": originalRequest.endDate, "expected_images": originalRequest.expectedImages]
        let dest = backup + "/" + (try string(c["group_name"])) + "/\(originalRequest.startDate)_\(originalRequest.endDate)_\(originalRequest.expectedImages)張"
        try require(try string(target["group_key"]) == group && equal(f, expected) && string(target["proposed_destination"]) == dest, .inconsistentAuthority)
        let producer = try object(report["producer"], keys: ["source_files", "source_sha256", "attestation"])
        try require(producer["attestation"] as? String == "UNKNOWN")
        let materials = producerSourceMaterial
        var expectedPaths = sourceNames.map { "src/line_backup_acceptance/" + $0 }
        if try int(s["schema_version"]) == 3 {
            expectedPaths += ["__init__.py", "__main__.py", "cli.py", "content.py", "coordinator.py", "image_decode.swift", "observations.py", "schema.py", "service.py", "state_v3.schema.json", "store.py"].map { "src/line_backup_batch/" + $0 }
            expectedPaths.append("scripts/line_backup_cua_adapter.mjs")
        }
        try require(materials.map(\.relativePath) == expectedPaths, .inconsistentSource)
        let digests = try array(producer["source_files"]); try require(digests.count == materials.count, .inconsistentSource)
        var aggregate = Data()
        for (i, m) in materials.enumerated() {
            try digest(digests[i], path: m.relativePath, bytes: m.rawBytes)
            aggregate.append(Data(m.relativePath.utf8)); aggregate.append(0); aggregate.append(m.rawBytes); aggregate.append(0)
        }
        try require(try string(producer["source_sha256"]) == hash(aggregate), .inconsistentSource)
        let facts = try object(report["state_facts"], keys: ["current_run_id", "current_run_terminal", "active_writer_id", "context_lock_present", "verified_match_run_ids", "verified_match_registry_count", "unresolved_run_ids", "purported_release_run_ids", "manual_archive_match", "destination_status"])
        try require(try bool(facts["manual_archive_match"]) == false)
        try require(equal(facts["current_run_id"]!, s["current_run_id"]!) && equal(facts["active_writer_id"]!, s["active_writer_id"]!), .inconsistentHistory)
        let current = runs.first { equal($0["run_id"]!, s["current_run_id"]!) }
        if let current { try require(try bool(facts["current_run_terminal"]) == terminal(current), .inconsistentHistory) }
        else { try require(isNull(facts["current_run_terminal"]), .inconsistentHistory) }
        try require(try bool(facts["context_lock_present"]) == !isNull(s["context_lock"]), .inconsistentHistory)
        let same = runs.filter { equal($0["fingerprint"]!, f) }
        let verified = same.filter { $0["workflow_outcome"] as? String == "VERIFIED" }.compactMap { $0["run_id"] as? String }.sorted()
        let registryCount = entries.filter { equal($0["fingerprint"]!, f) }.count
        let unresolvedIDs = try same.filter { try unresolved($0) }.compactMap { $0["run_id"] as? String }.sorted()
        let released = same.filter { ($0["reconciliations"] as? [Object] ?? []).contains { ($0["blocking_intent_released"] as? NSNumber)?.boolValue == true } }.compactMap { $0["run_id"] as? String }.sorted()
        try require(try strings(facts["verified_match_run_ids"]) == verified && int(facts["verified_match_registry_count"]) == registryCount && strings(facts["unresolved_run_ids"]) == unresolvedIDs && strings(facts["purported_release_run_ids"]) == released, .inconsistentHistory)
        let busy = try (s["active_batch"] != nil && !isNull(s["active_batch"])) || !isNull(s["active_writer_id"]) || !isNull(s["context_lock"]) || runs.contains { try !equal($0["fingerprint"]!, f) && unresolved($0) }
        let fingerprints = runs.compactMap { $0["fingerprint"] as? Object } + entries.compactMap { $0["fingerprint"] as? Object }
        let ambiguous = fingerprints.contains { $0["start_date"] as? String == originalRequest.startDate && $0["end_date"] as? String == originalRequest.endDate && !equal($0["expected_images"]!, f["expected_images"]!) }
        let ds = try string(facts["destination_status"])
        let decision: ProjectBackupInspectionDecision
        if busy { decision = .busy; try require(ds == "NOT_INSPECTED_BLOCKED") }
        else if !verified.isEmpty || registryCount > 0 { decision = .skipVerified; try require(ds == "NOT_INSPECTED_VERIFIED") }
        else if ambiguous { decision = .ambiguous; try require(ds == "NOT_INSPECTED_BLOCKED") }
        else if !unresolvedIDs.isEmpty { decision = .unresolved; try require(ds == "NOT_INSPECTED_BLOCKED") }
        else if ["NONEMPTY", "UNSAFE"].contains(ds) { decision = .destinationBlocked }
        else { decision = .eligible; try require(["ABSENT", "EMPTY"].contains(ds)) }
        try require(report["decision"] as? String == decision.rawValue, .inconsistentHistory)
        return ProjectBackupInspectionBinding(request: originalRequest, decision: decision, groupKey: group,
                                               proposedDestination: dest, stateRevision: try int(s["revision"]), stdoutSHA256: externalStdoutSHA256)
    }
}

/// Validate syntax with Foundation, but first reject duplicate decoded keys at every depth.
/// Escaped spellings such as "a" and "\u0061" denote the same key.
private struct DuplicateKeyScanner {
    let bytes: [UInt8]
    var index = 0
    mutating func whitespace() { while index < bytes.count && [9, 10, 13, 32].contains(bytes[index]) { index += 1 } }
    mutating func scan() throws {
        try value(depth: 0); whitespace()
        if index != bytes.count { throw ProjectBackupBindingError.invalidJSON }
    }
    mutating func quoted() throws -> String {
        let start = index; index += 1
        while index < bytes.count {
            let c = bytes[index]; index += 1
            if c == 92 { index += 1 }
            else if c == 34 {
                let data = Data(bytes[start..<index])
                guard let s = try JSONSerialization.jsonObject(with: data, options: .fragmentsAllowed) as? String else { throw ProjectBackupBindingError.invalidJSON }
                return s
            }
        }
        throw ProjectBackupBindingError.invalidJSON
    }
    mutating func take(_ c: UInt8) throws {
        whitespace(); guard index < bytes.count && bytes[index] == c else { throw ProjectBackupBindingError.invalidJSON }; index += 1
    }
    mutating func value(depth: Int) throws {
        whitespace(); guard index < bytes.count && depth < 128 else { throw ProjectBackupBindingError.invalidJSON }
        switch bytes[index] {
        case 123:
            index += 1; whitespace(); var keys = Set<String>()
            if index < bytes.count && bytes[index] == 125 { index += 1; return }
            while true {
                whitespace(); guard index < bytes.count && bytes[index] == 34 else { throw ProjectBackupBindingError.invalidJSON }
                let key = try quoted(); guard keys.insert(key).inserted else { throw ProjectBackupBindingError.invalidJSON }
                try take(58); try value(depth: depth + 1); whitespace()
                guard index < bytes.count else { throw ProjectBackupBindingError.invalidJSON }
                if bytes[index] == 125 { index += 1; return }; try take(44)
            }
        case 91:
            index += 1; whitespace()
            if index < bytes.count && bytes[index] == 93 { index += 1; return }
            while true {
                try value(depth: depth + 1); whitespace(); guard index < bytes.count else { throw ProjectBackupBindingError.invalidJSON }
                if bytes[index] == 93 { index += 1; return }; try take(44)
            }
        case 34: _ = try quoted()
        default:
            let start = index
            while index < bytes.count && ![9, 10, 13, 32, 44, 93, 125].contains(bytes[index]) { index += 1 }
            guard index > start else { throw ProjectBackupBindingError.invalidJSON }
        }
    }
}
