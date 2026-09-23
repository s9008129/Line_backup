// cg_window_list.swift — read-only on-screen window list (attempt-06).
//
// Purpose: report the window-server z-order (front to back) of on-screen
// windows with owner app, layer, bounds and window number, using only
// CGWindowListCopyWindowInfo. No input events, no AX writes, no app
// activation: a pure read-only query.
//
// Usage: cg_window_list [--json]
// Output: one deterministic JSON array on stdout (front-to-back order).

import Foundation
import CoreGraphics

let option = CGWindowListOption(arrayLiteral: .optionOnScreenOnly, .excludeDesktopElements)
guard let infoList = CGWindowListCopyWindowInfo(option, kCGNullWindowID) as? [[String: Any]] else {
    print("[]")
    exit(0)
}

func number(_ v: Any?) -> Any {
    if let d = v as? Double {
        if d.rounded() == d && abs(d) < 1e15 { return Int(d) }
        return (d * 1000).rounded() / 1000
    }
    if let i = v as? Int { return i }
    return NSNull()
}

var out: [[String: Any]] = []
for (index, w) in infoList.enumerated() {
    var rec: [String: Any] = ["z_index": index]
    rec["owner_name"] = w[kCGWindowOwnerName as String] ?? NSNull()
    rec["owner_pid"] = w[kCGWindowOwnerPID as String] ?? NSNull()
    rec["window_name"] = w[kCGWindowName as String] ?? NSNull()
    rec["layer"] = w[kCGWindowLayer as String] ?? NSNull()
    rec["window_number"] = w[kCGWindowNumber as String] ?? NSNull()
    rec["alpha"] = w[kCGWindowAlpha as String] ?? NSNull()
    if let b = w[kCGWindowBounds as String] as? [String: Any] {
        rec["bounds"] = ["x": number(b["X"]), "y": number(b["Y"]),
                         "width": number(b["Width"]), "height": number(b["Height"])]
    } else {
        rec["bounds"] = NSNull()
    }
    out.append(rec)
}

let data = try! JSONSerialization.data(withJSONObject: out, options: [.sortedKeys, .prettyPrinted])
print(String(data: data, encoding: .utf8)!)
