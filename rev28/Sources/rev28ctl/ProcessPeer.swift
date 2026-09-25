import Foundation
import Rev28Core

// JSON-lines peer over a child process's stdio pipes.

final class ProcessPeer {
    let name: String
    let process: Process
    private let stdinHandle: FileHandle
    private let replyLock = NSLock()
    private var replies: [String: [String: Any]] = [:]
    private let eventLock = NSLock()
    private var events: [[String: Any]] = []
    private var commandCounter = 0
    private var terminated = false

    init(executableURL: URL, arguments: [String], name: String, logURL: URL) throws {
        self.name = name
        let process = Process()
        process.executableURL = executableURL
        process.arguments = arguments
        let stdinPipe = Pipe()
        let stdoutPipe = Pipe()
        process.standardInput = stdinPipe
        process.standardOutput = stdoutPipe
        process.standardError = FileHandle.nullDevice
        self.process = process
        self.stdinHandle = stdinPipe.fileHandleForWriting
        try process.run()

        FileManager.default.createFile(atPath: logURL.path, contents: nil)
        let logHandle = try FileHandle(forWritingTo: logURL)
        LineReader(handle: stdoutPipe.fileHandleForReading, label: "\(name)-stdout") { [weak self] line in
            guard let self else { return }
            self.handle(line: line)
            if let data = (line + "\n").data(using: .utf8) {
                try? logHandle.write(contentsOf: data)
            }
        }.start()
    }

    private func handle(line: String) {
        guard let object = LineProtocol.decodeObject(line) else { return }
        if let id = object["id"] as? String {
            replyLock.lock()
            replies[id] = object
            replyLock.unlock()
        } else {
            eventLock.lock()
            events.append(object)
            eventLock.unlock()
        }
    }

    private func takeReply(id: String) -> [String: Any]? {
        replyLock.lock()
        defer { replyLock.unlock() }
        return replies.removeValue(forKey: id)
    }

    private func pushFront(_ items: [[String: Any]]) {
        eventLock.lock()
        events.insert(contentsOf: items, at: 0)
        eventLock.unlock()
    }

    private func drainEventsLocked() -> [[String: Any]] {
        eventLock.lock()
        defer { eventLock.unlock() }
        let drained = events
        events = []
        return drained
    }

    func send(_ command: String, params: [String: Any] = [:], timeoutSeconds: Double = 15.0) async throws -> [String: Any] {
        commandCounter += 1
        let id = "c\(commandCounter)"
        var object: [String: Any] = ["id": id, "cmd": command]
        if !params.isEmpty { object["params"] = params }
        guard let line = LineProtocol.jsonString(object) else {
            throw NSError(domain: "rev28ctl", code: 1, userInfo: [NSLocalizedDescriptionKey: "failed to encode command \(command)"])
        }
        if let data = (line + "\n").data(using: .utf8) {
            try stdinHandle.write(contentsOf: data)
        }
        let deadline = Date().addingTimeInterval(timeoutSeconds)
        while Date() < deadline {
            if let reply = takeReply(id: id) { return reply }
            try await Task.sleep(nanoseconds: 15_000_000)
        }
        throw NSError(
            domain: "rev28ctl",
            code: 2,
            userInfo: [NSLocalizedDescriptionKey: "\(name): timeout waiting for reply to \(command)"]
        )
    }

    func drainEvents() -> [[String: Any]] {
        drainEventsLocked()
    }

    func waitForEvent(_ name: String, timeoutSeconds: Double) async -> [String: Any]? {
        let deadline = Date().addingTimeInterval(timeoutSeconds)
        while Date() < deadline {
            let drained = drainEventsLocked()
            var match: [String: Any]?
            var others: [[String: Any]] = []
            for event in drained {
                if match == nil, (event["event"] as? String) == name {
                    match = event
                } else {
                    others.append(event)
                }
            }
            if !others.isEmpty {
                pushFront(others)
            }
            if let match { return match }
            try? await Task.sleep(nanoseconds: 20_000_000)
        }
        return nil
    }

    var isRunning: Bool { process.isRunning }

    func terminate() {
        guard !terminated else { return }
        terminated = true
        if let line = LineProtocol.jsonString(["id": "quit", "cmd": "quit"]),
           let data = (line + "\n").data(using: .utf8) {
            try? stdinHandle.write(contentsOf: data)
        }
        if process.isRunning {
            process.terminate()
        }
    }
}
