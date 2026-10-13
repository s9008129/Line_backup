public struct FrameSupportGrantProfile: Equatable {
    public let taskID: String
    public let contractPath: String
    public let contractSHA256: String
    public let artifactDirectory: String
    public let taskModules: [String]
    public let isMinimalLive08: Bool

    private init(taskID: String, contractPath: String, contractSHA256: String,
                 artifactDirectory: String, taskModules: [String], isMinimalLive08: Bool) {
        self.taskID = taskID
        self.contractPath = contractPath
        self.contractSHA256 = contractSHA256
        self.artifactDirectory = artifactDirectory
        self.taskModules = taskModules
        self.isMinimalLive08 = isMinimalLive08
    }

    public func acceptsGrantPath(_ path: String) -> Bool {
        if isMinimalLive08 {
            return ["live-grant-1.json", "live-grant-2.json"].contains {
                path == "\(artifactDirectory)/\($0)"
            }
        }
        return path.hasPrefix("harness-development/")
    }

    public static let legacy = FrameSupportGrantProfile(
        taskID: "TASK-20261010-line-v3-live-e2e",
        contractPath: "harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/plan-contract.json",
        contractSHA256: "d46984fd70e41dde29974280e8054fcbd08c863030df926e5f0f3739f36fd219",
        artifactDirectory: "harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03",
        taskModules: [
            "harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/chooser_locators.mjs",
            "harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/live_classifier.mjs",
            "harness-development/line-v3-live-e2e-20261010/continuations/live-grounding-03/live_runner.mjs",
            "scripts/line_backup_cua_adapter.mjs",
        ].sorted(),
        isMinimalLive08: false
    )

    public static let minimalLive08 = FrameSupportGrantProfile(
        taskID: "TASK-4acb4326ea2a4c50ace6f333f2de8751",
        contractPath: "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/controller/TASK-4acb4326ea2a4c50ace6f333f2de8751/plan-contract.json",
        contractSHA256: "a043df49903b41b5102d671ca5afb252d73de0d8f796c8bc3749a7b41873dffc",
        artifactDirectory: "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08",
        taskModules: [
            "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/checks/validate_real_frame.py",
            "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/chooser_locators.mjs",
            "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/host_io.mjs",
            "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/live_analyzer.mjs",
            "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/live_classifier.mjs",
            "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/live_entry.mjs",
            "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/live_runner.mjs",
            "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/tools/host_process.py",
            "harness-development/line-v3-live-e2e-20261010/continuations/minimal-live-08/tools/retain_payload.py",
            "scripts/line_backup_cua_adapter.mjs",
        ].sorted(),
        isMinimalLive08: true
    )

    public static func select(taskID: String, contractPath: String, contractSHA256: String,
                              artifactDirectory: String) -> FrameSupportGrantProfile? {
        [legacy, minimalLive08].first {
            $0.taskID == taskID
                && $0.contractPath == contractPath
                && $0.contractSHA256 == contractSHA256
                && $0.artifactDirectory == artifactDirectory
        }
    }
}
