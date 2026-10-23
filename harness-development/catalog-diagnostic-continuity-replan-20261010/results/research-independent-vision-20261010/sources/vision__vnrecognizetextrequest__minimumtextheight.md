<!--
{
  "availability" : [
    "iOS: 13.0.0 -",
    "iPadOS: 13.0.0 -",
    "macCatalyst: 13.1.0 -",
    "macOS: 10.15.0 -",
    "tvOS: 13.0.0 -",
    "visionOS: 1.0.0 -"
  ],
  "documentType" : "symbol",
  "framework" : "Vision",
  "identifier" : "/documentation/Vision/VNRecognizeTextRequest/minimumTextHeight",
  "metadataVersion" : "0.1.0",
  "role" : "Instance Property",
  "symbol" : {
    "kind" : "Instance Property",
    "modules" : [
      "Vision"
    ],
    "preciseIdentifier" : "c:objc(cs)VNRecognizeTextRequest(py)minimumTextHeight"
  },
  "title" : "minimumTextHeight"
}
-->

# minimumTextHeight

The minimum height, relative to the image height, of the text to recognize.

```
var minimumTextHeight: Float { get set }
```

## Discussion

Specify a floating-point number relative to the image height. For example, to limit recognition to text that’s half of the image height, use `0.5`. Increasing the size reduces memory consumption and expedites recognition with the tradeoff of ignoring text smaller than the minimum height. The default value is 1/32, or `0.03125`.

---

Copyright &copy; 2026 Apple Inc. All rights reserved. | [Terms of Use](https://www.apple.com/legal/internet-services/terms/site.html) | [Privacy Policy](https://www.apple.com/privacy/privacy-policy)