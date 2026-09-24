import Foundation
import CoreGraphics
import ApplicationServices
import ScreenCaptureKit

let screenCapturePreflight = CGPreflightScreenCaptureAccess()
let postEventPreflight = CGPreflightPostEventAccess()
let axTrusted = AXIsProcessTrusted()
print("CGPreflightScreenCaptureAccess=\(screenCapturePreflight)")
print("CGPreflightPostEventAccess=\(postEventPreflight)")
print("AXIsProcessTrusted=\(axTrusted)")

let sem = DispatchSemaphore(value: 0)
Task {
    do {
        let content = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: true)
        var lineCount = 0
        for w in content.windows {
            if w.owningApplication?.bundleIdentifier == "jp.naver.line.mac" { lineCount += 1 }
        }
        print("SCShareableContent.OK windows=\(content.windows.count) apps=\(content.applications.count) displays=\(content.displays.count) lineWindows=\(lineCount)")
        for w in content.windows.prefix(8) {
            print("  win id=\(w.windowID) app=\(w.owningApplication?.bundleIdentifier ?? "?") frame=\(w.frame) title=\(w.title ?? "") onScreen=\(w.isOnScreen)")
        }
    } catch {
        print("SCShareableContent.ERROR \(error)")
    }
    sem.signal()
}
sem.wait()
