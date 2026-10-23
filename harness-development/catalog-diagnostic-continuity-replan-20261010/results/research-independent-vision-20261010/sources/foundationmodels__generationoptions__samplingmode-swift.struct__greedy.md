<!--
{
  "availability" : [
    "iOS: 26.0.0 -",
    "iPadOS: 26.0.0 -",
    "macCatalyst: 26.0.0 -",
    "macOS: 26.0.0 -",
    "visionOS: 26.0.0 -",
    "watchOS: 27.0.0 -"
  ],
  "documentType" : "symbol",
  "framework" : "FoundationModels",
  "identifier" : "/documentation/FoundationModels/GenerationOptions/SamplingMode-swift.struct/greedy",
  "metadataVersion" : "0.1.0",
  "role" : "Type Property",
  "symbol" : {
    "kind" : "Type Property",
    "modules" : [
      "Foundation Models",
      "FoundationModels"
    ],
    "preciseIdentifier" : "s:16FoundationModels17GenerationOptionsV12SamplingModeV6greedyAEvpZ"
  },
  "title" : "greedy"
}
-->

# greedy

A sampling mode that always chooses the most likely token.

```
static var greedy: GenerationOptions.SamplingMode { get }
```

## Discussion

This mode always produces the same output
for a given input. Responses produced with greedy sampling
are statistically likely, but may lack the human-like quality
and variety of other sampling strategies.

> SeeAlso: Sampling modes ``doc://com.apple.foundationmodels/documentation/FoundationModels/GenerationOptions/SamplingMode-swift.struct/random(top:seed:)`` and ``doc://com.apple.foundationmodels/documentation/FoundationModels/GenerationOptions/SamplingMode-swift.struct/random(probabilityThreshold:seed:)``

---

Copyright &copy; 2026 Apple Inc. All rights reserved. | [Terms of Use](https://www.apple.com/legal/internet-services/terms/site.html) | [Privacy Policy](https://www.apple.com/privacy/privacy-policy)