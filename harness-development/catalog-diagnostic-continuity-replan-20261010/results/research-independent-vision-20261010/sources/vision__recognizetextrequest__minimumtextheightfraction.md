<!--
{
  "availability" : [
    "iOS: 18.0.0 -",
    "iPadOS: 18.0.0 -",
    "macOS: 15.0.0 -",
    "tvOS: 18.0.0 -",
    "visionOS: 2.0.0 -"
  ],
  "documentType" : "symbol",
  "framework" : "Vision",
  "identifier" : "/documentation/Vision/RecognizeTextRequest/minimumTextHeightFraction",
  "metadataVersion" : "0.1.0",
  "role" : "Instance Property",
  "symbol" : {
    "kind" : "Instance Property",
    "modules" : [
      "Vision"
    ],
    "preciseIdentifier" : "s:6Vision20RecognizeTextRequestV07minimumC14HeightFractionSfvp"
  },
  "title" : "minimumTextHeightFraction"
}
-->

# minimumTextHeightFraction

The minimum height, relative to the image height, of the text to recognize.

```
var minimumTextHeightFraction: Float
```

## Discussion

Specify a floating-point number relative to the image height. For example, to limit recognition to text that’s half of the image height, use `0.5`. Increasing the size reduces memory consumption and expedites recognition with the tradeoff of ignoring text smaller than the minimum height. The default value is `1/32`, or `0.03125`.

---

Copyright &copy; 2026 Apple Inc. All rights reserved. | [Terms of Use](https://www.apple.com/legal/internet-services/terms/site.html) | [Privacy Policy](https://www.apple.com/privacy/privacy-policy)