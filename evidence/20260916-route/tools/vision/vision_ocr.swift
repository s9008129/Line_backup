import Foundation
import Vision
import AppKit

let args = CommandLine.arguments
guard args.count >= 2 else { print("usage: vision_ocr <image>"); exit(2) }
let url = URL(fileURLWithPath: args[1])
guard let img = NSImage(contentsOf: url), let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    print("LOAD_FAIL \(args[1])"); exit(3)
}
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.recognitionLanguages = ["zh-Hant", "en-US"]
req.usesLanguageCorrection = false
let handler = VNImageRequestHandler(cgImage: cg, options: [:])
do { try handler.perform([req]) } catch { print("OCR_FAIL \(error)"); exit(4) }
let W = Double(cg.width), H = Double(cg.height)
for obs in (req.results ?? []) {
    guard let c = obs.topCandidates(1).first else { continue }
    let bb = obs.boundingBox
    let x0 = bb.origin.x * W, w = bb.size.width * W
    let y1 = (1 - bb.origin.y) * H, h = bb.size.height * H
    let y0 = y1 - h
    print(String(format: "px[%.0f,%.0f,%.0f,%.0f]\tconf=%.2f\t%@", x0, y0, x0+w, y0+h, c.confidence, c.string))
}
