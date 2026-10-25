import ApplicationServices
import CoreGraphics
import Darwin
import Foundation
import Rev28Core
import Vision

/// The project pilot is a separate authority, never a renamed legacy grant.
/// Reuse the canonical Python project authorizer for every native observation.
enum PilotNativeAuthority {
    static let profile = "LINE_TWO_ALBUM_PILOT/1"
    static let directory = "harness-development/line-two-album-pilot-20261014/private"

    static func read(_ relative: String, root: URL) throws -> Data {
        guard !relative.hasPrefix("/"), relative.split(separator: "/", omittingEmptySubsequences: false)
            .allSatisfy({ !$0.isEmpty && $0 != "." && $0 != ".." }) else {
            throw PassiveDiagnosticError.refused("pilot relative path required")
        }
        return try PassiveNativeDiagnostic.readProjectRegularFile(
            path: root.appendingPathComponent(relative).path, projectRoot: root.path)
    }

    static func json(_ raw: Data) throws -> [String: Any] {
        guard let value = try JSONSerialization.jsonObject(with: raw) as? [String: Any] else {
            throw PassiveDiagnosticError.refused("pilot object required")
        }
        return value
    }

    static func bound(_ ref: [String: Any], root: URL) throws -> Data {
        guard Set(ref.keys) == Set(["path", "bytes", "sha256"]), let path = ref["path"] as? String,
              let size = ref["bytes"] as? Int, let hash = ref["sha256"] as? String else {
            throw PassiveDiagnosticError.refused("pilot file binding required")
        }
        let raw = try read(path, root: root)
        guard raw.count == size, EvidenceIO.sha256Hex(raw) == hash else {
            throw PassiveDiagnosticError.refused("pilot bound file drift")
        }
        return raw
    }

    static func one56Bundle(_ grantPath: String) -> String? {
        let parts = grantPath.split(separator: "/", omittingEmptySubsequences: false).map(String.init)
        let base = directory.split(separator: "/").map(String.init)
        guard parts.count == base.count + 3,
              Array(parts.prefix(base.count)) == base,
              parts[base.count] == "authority-bundles",
              parts[base.count + 2] == "project-grant.json",
              parts.joined(separator: "/") == grantPath else { return nil }
        let name = parts[base.count + 1]
        guard name.hasPrefix("ONE56-"), name.count <= 70,
              let first = name.dropFirst(6).first,
              first.isASCII && (first.isLetter || first.isNumber),
              name.dropFirst(6).allSatisfy({ $0.isASCII && ($0.isLetter || $0.isNumber || $0 == "_" || $0 == "-") })
        else { return nil }
        return parts.dropLast().joined(separator: "/")
    }

    static func verify(root: URL, grantPath: String, grantSHA: String,
                       surface: String? = nil, sessionID: String? = nil) throws -> [String: Any] {
        guard grantPath.hasPrefix(directory + "/"),
              root.path == FileManager.default.currentDirectoryPath else {
            throw PassiveDiagnosticError.refused("pilot grant/root scope mismatch")
        }
        let raw = try read(grantPath, root: root)
        guard EvidenceIO.sha256Hex(raw) == grantSHA else {
            throw PassiveDiagnosticError.refused("pilot grant digest mismatch")
        }
        let grant = try json(raw)
        let one56 = grant["single_album_route"] as? Bool == true
        let bundle = one56 ? one56Bundle(grantPath) : nil
        let expectedContract = one56 ? bundle.map { $0 + "/project-contract.json" } : directory + "/project-contract.json"
        guard (!one56 || bundle != nil),
              grant["grant_version"] as? String == "line-two-album-project-grant-1",
              grant["project_profile"] as? String == profile,
              grant["project_root"] as? String == root.path,
              let owner = grant["owner"] as? String, !owner.isEmpty,
              sessionID == nil || sessionID == owner,
              grant["contract_path"] as? String == expectedContract,
              let contractSHA = grant["contract_sha256"] as? String,
              let producer = grant["producer_binary"] as? [String: Any],
              let scope = grant["sensor_scope"] as? [String: Any],
              scope["bundle_id"] as? String == "jp.naver.line.mac",
              scope["provider"] as? String == "SCREEN_CAPTURE_KIT",
              scope["capture_scope"] as? String == "FULL_DISPLAY",
              let surfaces = scope["surfaces"] as? [String],
              surface == nil || surfaces.contains(surface!) else {
            throw PassiveDiagnosticError.refused("pilot native authority scope mismatch")
        }
        let actualContractRaw = try read(expectedContract!, root: root)
        guard EvidenceIO.sha256Hex(actualContractRaw) == contractSHA else {
            throw PassiveDiagnosticError.refused("pilot contract digest mismatch")
        }
        let contract = try json(actualContractRaw)
        if one56 {
            guard let bundle,
                  let decision = grant["owner_decision"] as? [String: Any],
                  let review = grant["external_review"] as? [String: Any],
                  let readiness = grant["live_readiness"] as? [String: Any],
                  let runtime = grant["runtime_binding"] as? [String: Any],
                  decision["path"] as? String == bundle + "/owner-decision.json",
                  review["path"] as? String == bundle + "/implementation-review.json",
                  readiness["path"] as? String == bundle + "/live-readiness.json",
                  runtime["path"] as? String == bundle + "/runtime-binding.json" else {
                throw PassiveDiagnosticError.refused("one56 authority bundle references are mixed")
            }
            _ = try bound(decision, root: root)
            let reviewRaw = try bound(review, root: root)
            let reviewObject = try json(reviewRaw)
            guard let originalReview = reviewObject["original_review_ref"] as? [String: Any],
                  originalReview["path"] as? String == bundle + "/external-review-original.json",
                  let providerResponse = reviewObject["provider_response_ref"] as? [String: Any],
                  providerResponse["path"] as? String == bundle + "/github-review-response.json" else {
                throw PassiveDiagnosticError.refused("one56 original external review reference is mixed")
            }
            _ = try bound(originalReview, root: root)
            _ = try bound(providerResponse, root: root)
            _ = try bound(runtime, root: root)
            let readinessRaw = try bound(readiness, root: root)
            let readinessObject = try json(readinessRaw)
            guard let consent = readinessObject["owner_consent_ref"] as? [String: Any],
                  consent["path"] as? String == bundle + "/owner-consent.json" else {
                throw PassiveDiagnosticError.refused("one56 owner consent bundle reference is mixed")
            }
            _ = try bound(consent, root: root)
        }
        guard let authorizer = contract["native_authorizer"] as? [String: Any],
              let python = authorizer["python"] as? [String: Any],
              let pythonPath = python["path"] as? String,
              pythonPath.hasPrefix("/opt/homebrew/Cellar/python@3.13/"),
              let pythonSHA = python["sha256"] as? String,
              let dependencyPath = authorizer["dependency_path"] as? String,
              dependencyPath.hasPrefix("harness-development/"),
              !dependencyPath.split(separator: "/").contains(".."),
              let dependencies = authorizer["dependencies"] as? [[String: Any]], !dependencies.isEmpty else {
            throw PassiveDiagnosticError.refused("pilot pinned Python/dependencies missing")
        }
        let pythonURL = URL(fileURLWithPath: pythonPath)
        guard pythonURL.resolvingSymlinksInPath().path == pythonPath,
              EvidenceIO.sha256Hex(try Data(contentsOf: pythonURL)) == pythonSHA else {
            throw PassiveDiagnosticError.refused("pilot Python runtime drift")
        }
        for dependency in dependencies {
            guard let path = dependency["path"] as? String, path.hasPrefix(dependencyPath + "/") else {
                throw PassiveDiagnosticError.refused("pilot dependency scope mismatch")
            }
            _ = try bound(dependency, root: root)
        }
        let binary = try bound(producer, root: root)
        let running = URL(fileURLWithPath: CommandLine.arguments[0]).resolvingSymlinksInPath()
        guard let path = producer["path"] as? String,
              running.path == root.appendingPathComponent(path).path,
              EvidenceIO.sha256Hex(try Data(contentsOf: running)) == EvidenceIO.sha256Hex(binary) else {
            throw PassiveDiagnosticError.refused("running binary is not the pilot producer")
        }
        let process = Process()
        process.executableURL = pythonURL
        process.arguments = ["-B", "-m", "line_backup_batch.cli", "native_authorize",
                             "--project-root", root.path, "--authorization", grantPath]
        process.currentDirectoryURL = root
        process.environment = ["PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1", "PYTHONPATH": root.appendingPathComponent("src").path + ":" + root.appendingPathComponent(dependencyPath).path]
        let output = Pipe(), errors = Pipe(), finished = DispatchSemaphore(value: 0)
        process.standardInput = FileHandle.nullDevice
        process.standardOutput = output; process.standardError = errors
        process.terminationHandler = { _ in finished.signal() }
        try process.run()
        guard finished.wait(timeout: .now() + 30) == .success else {
            process.terminate()
            if finished.wait(timeout: .now() + 1) != .success { kill(process.processIdentifier, SIGKILL) }
            process.waitUntilExit()
            throw PassiveDiagnosticError.refused("pilot authorizer timed out; no native observation")
        }
        let response = output.fileHandleForReading.readDataToEndOfFile()
        guard process.terminationStatus == 0, response.count < 65_536 else {
            throw PassiveDiagnosticError.refused("canonical pilot authorizer refused; no native observation")
        }
        let accepted = try json(response)
        guard accepted["status"] as? String == "PROJECT_NATIVE_AUTHORIZED",
              accepted["owner"] as? String == owner,
              accepted["task_id"] as? String == grant["task_id"] as? String,
              accepted["source_sha256"] as? String == grant["source_sha256"] as? String,
              accepted["project_root"] as? String == root.path,
              accepted["native_controller_admission"] as? Bool == false else {
            throw PassiveDiagnosticError.refused("pilot authorizer response binding mismatch")
        }
        guard try read(grantPath, root: root) == raw else {
            throw PassiveDiagnosticError.refused("pilot grant changed during authorization")
        }
        guard CGPreflightScreenCaptureAccess(), AXIsProcessTrusted() else {
            throw PassiveDiagnosticError.refused("native screen capture/accessibility permission missing")
        }
        return grant
    }

    /// No target app acquisition, AX read, screenshot, grant or ledger mutation.
    static func preflight() throws -> [String: Any] {
        let executable = URL(fileURLWithPath: CommandLine.arguments[0]).resolvingSymlinksInPath()
        let languages = try VNRecognizeTextRequest().supportedRecognitionLanguages()
        return ["status": "NATIVE_RUNTIME_PREFLIGHT", "screen_capture_authorized": CGPreflightScreenCaptureAccess(),
            "accessibility_authorized": AXIsProcessTrusted(), "vision_languages": languages,
            "binary_sha256": EvidenceIO.sha256Hex(try Data(contentsOf: executable)),
            "project_authorization_route": profile, "native_controller_admission": false,
            "line_observation_performed": false, "gui_inputs": 0]
    }
}
