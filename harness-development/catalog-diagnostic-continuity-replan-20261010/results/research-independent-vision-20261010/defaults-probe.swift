import Foundation
import Vision
let modern = RecognizeTextRequest()
let legacy = VNRecognizeTextRequest()
print("modern.minimumTextHeightFraction=\(modern.minimumTextHeightFraction)")
print("modern.revision=\(modern.revision)")
print("legacy.minimumTextHeight=\(legacy.minimumTextHeight)")
print("legacy.revision=\(legacy.revision)")
print("modern.languages=\(modern.supportedRecognitionLanguages)")
print("legacy.languages=\(try legacy.supportedRecognitionLanguages())")
print("recognition_calls=0; image_inputs=0; ui_inputs=0")
