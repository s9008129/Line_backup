import AppKit
import Foundation
import Rev28Core

let application = NSApplication.shared
let harness = HarnessController()
application.delegate = harness
application.run()
