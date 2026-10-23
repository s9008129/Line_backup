<!--
{
  "documentType" : "article",
  "framework" : "Vision",
  "identifier" : "/documentation/Vision/recognizing-text-in-images",
  "metadataVersion" : "0.1.0",
  "role" : "article",
  "title" : "Recognizing Text in Images"
}
-->

# Recognizing Text in Images

Add text-recognition features to your app using the Vision framework.

## Discussion

One of Vision’s many powerful features is its ability to detect and recognize multilanguage text in images. You can use this functionality in your own apps to handle both real-time and offline use cases. In all cases, all of Vision’s processing happens on the user’s device to enhance performance and user privacy.

Vision’s text-recognition capabilities operate using one of these paths:

- Fast: The fast path uses the framework’s character-detection capabilities to find individual characters, and then uses a small machine learning model to recognize individual characters and words. This approach is similar to traditional optical character recognition (OCR).

For example code using the fast path, see [Extracting phone numbers from text in images](/documentation/Vision/extracting-phone-numbers-from-text-in-images).

- Accurate: The accurate path uses a neural network to find text in terms of strings and lines, and then performs further analysis to find individual words and sentences. This approach is much more in line with how humans read text.

For example code using the accurate path, see <doc://com.apple.documentation/documentation/VisionKit/structuring-recognized-text-on-a-document>.

Using either path, you may optionally apply a language-correction phase based on Natural Language Processing (NLP) to minimize the potential for misreadings.

![An illustration contrasting the Vision framework’s fast text-recognition path with its accurate text-recognition path. ](images/Vision/media-3616311@2x.png)

> Note:
> Using Vision’s text-recognition features is similar to performing other Vision operations, where you perform computer vision requests on an image and retrieve the resulting observations. If you’re new to the Vision framework, see <doc://Vision/documentation/Vision/detecting-objects-in-still-images>.

### Perform a Text-Recognition Request

Vision provides its text-recognition capabilities through [`VNRecognizeTextRequest`](/documentation/Vision/VNRecognizeTextRequest), an image-based request type that finds and extracts text in images. The following example shows how to use [`VNImageRequestHandler`](/documentation/Vision/VNImageRequestHandler) to perform a [`VNRecognizeTextRequest`](/documentation/Vision/VNRecognizeTextRequest) for recognizing text in the specified <doc://com.apple.documentation/documentation/CoreGraphics/CGImage>.

```swift
// Get the CGImage on which to perform requests.
guard let cgImage = UIImage(named: "snapshot")?.cgImage else { return }

// Create a new image-request handler.
let requestHandler = VNImageRequestHandler(cgImage: cgImage)

// Create a new request to recognize text.
let request = VNRecognizeTextRequest(completionHandler: recognizeTextHandler)

do {
    // Perform the text-recognition request.
    try requestHandler.perform([request])
} catch {
    print("Unable to perform the requests: \(error).")
}
```

> Note:
> ``doc://Vision/documentation/Vision/VNRecognizeTextRequest`` uses the accurate path by default. To select the fast path, set the request’s ``doc://Vision/documentation/Vision/VNRecognizeTextRequest/recognitionLevel`` property to ``doc://Vision/documentation/Vision/VNRequestTextRecognitionLevel/fast``.

### Process the Results

After the request handler processes the request, it calls the request’s completion closure, passing it the request and any errors that occurred. Retrieve the observations by querying the request object for its [`results`](/documentation/Vision/VNRequest/results), which it returns as an array of [`VNRecognizedTextObservation`](/documentation/Vision/VNRecognizedTextObservation) objects. Each observation provides the recognized text string, along with a confidence score that indicates the confidence in the accuracy of the recognition.

```swift
func recognizeTextHandler(request: VNRequest, error: Error?) {
    guard let observations =
            request.results as? [VNRecognizedTextObservation] else {
        return
    }
    let recognizedStrings = observations.compactMap { observation in
        // Return the string of the top VNRecognizedText instance.
        return observation.topCandidates(1).first?.string
    }
    
    // Process the recognized strings.
    processResults(recognizedStrings)
}
```

If you’d like to render the bounding rectangles around recognized text in your user interface, you can also retrieve that information from the observation. The rectangles it provides are in normalized coordinates. To render them correctly in your user interface, convert <doc://com.apple.documentation/documentation/CoreFoundation/CGRect> instances from normalized coordinates to image coordinates by using the [`VNImageRectForNormalizedRect(_:_:_:)`](/documentation/Vision/VNImageRectForNormalizedRect(_:_:_:)) function as shown below.

```swift
let boundingRects: [CGRect] = observations.compactMap { observation in

    // Find the top observation.
    guard let candidate = observation.topCandidates(1).first else { return .zero }
    
    // Find the bounding-box observation for the string range.
    let stringRange = candidate.string.startIndex..<candidate.string.endIndex
    let boxObservation = try? candidate.boundingBox(for: stringRange)
    
    // Get the normalized CGRect value.
    let boundingBox = boxObservation?.boundingBox ?? .zero
    
    // Convert the rectangle from normalized coordinates to image coordinates.
    return VNImageRectForNormalizedRect(boundingBox,
                                        Int(image.size.width),
                                        Int(image.size.height))
}
```

The resulting bounding box differs depending on the path you choose. The fast path calculates the recognized text’s bounding rectangle based on its individual characters. The accurate path tokenizes on whitespace, which means when working with Chinese text, the resulting bounding boxes will likely contain lines or line fragments instead of complete text.

### Optimize Language Settings

Your choice of fast or accurate path, along with your use of a particular API revision, determines the language support the text-recognition algorithms provide. To determine which languages a particular path and revision support, call the request’s [`supportedRecognitionLanguages(for:revision:)`](/documentation/Vision/VNRecognizeTextRequest/supportedRecognitionLanguages(for:revision:)) class method.

If not otherwise specified, Vision biases its results toward English. To alter its default behavior, provide an array of supported languages in the request’s [`recognitionLanguages`](/documentation/Vision/VNRecognizeTextRequest/recognitionLanguages) property. The order in which you provide the languages dictates their relative importance. To recognize traditional and simplified Chinese, specify `zh-Hant` and `zh-Hans` as the first elements in the request’s [`recognitionLanguages`](/documentation/Vision/VNRecognizeTextRequest/recognitionLanguages) property. English is the only other language that you can pair with Chinese.

Enabling language correction on the request helps minimize common recognition errors. If the text you’re recognizing uses domain-specific jargon, such as medical or technical terms, you can tailor the language correction’s behavior by setting the request’s [`customWords`](/documentation/Vision/VNRecognizeTextRequest/customWords) property. Language correction gives precedence to the custom words when performing its processing. The request ignores the [`customWords`](/documentation/Vision/VNRecognizeTextRequest/customWords) property if language correction isn’t enabled.

> Note:
> Vision doesn’t support language correction, or its related ``doc://Vision/documentation/Vision/VNRecognizeTextRequest/customWords`` array, for Chinese.

---

Copyright &copy; 2026 Apple Inc. All rights reserved. | [Terms of Use](https://www.apple.com/legal/internet-services/terms/site.html) | [Privacy Policy](https://www.apple.com/privacy/privacy-policy)