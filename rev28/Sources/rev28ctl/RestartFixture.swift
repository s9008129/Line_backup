import Foundation
import Rev28Core

// Item 9 fixture: rev28ctl kills itself with SIGKILL at scripted points after an
// intent append, so the parent can prove crash-resume is observe-only and the
// ledger hash chain survives.

enum RestartFixture {
    static func runChild(arguments: [String]) -> Int32 {
        var ledgerPath: String?
        var headPath: String?
        var point: String?
        var index = 0
        while index < arguments.count {
            let argument = arguments[index]
            switch argument {
            case "--ledger":
                index += 1
                ledgerPath = index < arguments.count ? arguments[index] : nil
            case "--head-file":
                index += 1
                headPath = index < arguments.count ? arguments[index] : nil
            case "--point":
                index += 1
                point = index < arguments.count ? arguments[index] : nil
            default:
                break
            }
            index += 1
        }
        guard let ledgerPath, let point else {
            FileHandle.standardError.write(Data("restart-child: --ledger and --point are required\n".utf8))
            return 64
        }
        let ledgerURL = URL(fileURLWithPath: ledgerPath)
        do {
            let ledger = try IntentLedger(fileURL: ledgerURL)
            for entry in ledger.entries {
                if LedgerResume.irreversibleKinds.contains(entry.kind) {
                    _ = try ledger.append(kind: "resume.observeOnly", payload: ["priorDispatchSeq": String(entry.seq), "fixture": "restart-child"])
                }
            }
            _ = try ledger.append(kind: "intent.saved", payload: ["fixture": point])

            switch point {
            case "afterIntentFsync":
                break
            case "afterDispatch":
                _ = try ledger.append(kind: "dispatch.irreversible", payload: ["fixture": point, "surface": "synthetic"])
            case "midPostcondition":
                _ = try ledger.append(kind: "dispatch.saveAll", payload: ["fixture": point, "surface": "synthetic"])
                _ = try ledger.append(kind: "postcondition.armed", payload: ["bounds": "plan-time"])
                usleep(250_000)
            case "midDownload":
                _ = try ledger.append(kind: "dispatch.saveAll", payload: ["fixture": point, "surface": "synthetic"])
                let partial = ledgerURL.deletingLastPathComponent().appendingPathComponent("download-partial-\(point).bin")
                try Data(repeating: 0x41, count: 512).write(to: partial, options: .atomic)
                _ = try ledger.append(kind: "download.inProgress", payload: ["path": partial.path, "bytes": "512"])
                usleep(120_000)
            default:
                break
            }

            if let headPath {
                let headObject: [String: Any] = [
                    "seq": ledger.entries.count,
                    "headHash": ledger.headHash ?? "",
                    "pid": Int(getpid()),
                    "point": point,
                    "atISO8601": EvidenceIO.iso8601(),
                ]
                if let data = try? JSONSerialization.data(withJSONObject: headObject, options: [.sortedKeys]) {
                    _ = try? EvidenceIO.writeAtomically(data, to: URL(fileURLWithPath: headPath), appendOnly: true)
                }
            }
            // Scripted crash point: SIGKILL after the intent fsync.
            kill(getpid(), SIGKILL)
            return 0
        } catch {
            FileHandle.standardError.write(Data("restart-child failed: \(error)\n".utf8))
            return 70
        }
    }
}
