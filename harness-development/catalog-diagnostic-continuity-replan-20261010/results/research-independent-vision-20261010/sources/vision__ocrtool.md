<!--
{
  "availability" : [
    "iOS: 27.0.0 -",
    "iPadOS: 27.0.0 -",
    "macOS: 27.0.0 -",
    "visionOS: 27.0.0 -"
  ],
  "documentType" : "symbol",
  "framework" : "Vision",
  "identifier" : "/documentation/Vision/OCRTool",
  "metadataVersion" : "0.1.0",
  "role" : "Structure",
  "symbol" : {
    "kind" : "Structure",
    "modules" : [
      "Vision",
      "FoundationModels"
    ],
    "preciseIdentifier" : "s:24_Vision_FoundationModels7OCRToolV"
  },
  "title" : "OCRTool"
}
-->

# OCRTool

A tool that recognizes text in an image.

```
struct OCRTool
```

## Overview

The tool returns a string containing all recognized text from the image. To enable this tool, configure your
`LanguageModelSession` with an instance of `OCRTool`.

```swift
let ocrTool = OCRTool()
let session = LanguageModelSession(tools: [ocrTool])
```

You can override the default name and description to customize how the model
identifies and uses the tool.

```swift
let customTool = OCRTool(
    name: "extractText",
    description: "Extract text from documents"
)
```

> Note:
> ``doc://Vision/documentation/Vision/OCRTool`` isn’t available in Simulator.

## Topics

### Creating a tool

[`init(name: String?, description: String?)`](/documentation/Vision/OCRTool/init(name:description:))

Creates a tool for recognizing text in images.

## Relationships

### Conforms To

[`Sendable`](/documentation/Swift/Sendable)

[`SendableMetatype`](/documentation/Swift/SendableMetatype)

[`Tool`](/documentation/FoundationModels/Tool)

---

Copyright &copy; 2026 Apple Inc. All rights reserved. | [Terms of Use](https://www.apple.com/legal/internet-services/terms/site.html) | [Privacy Policy](https://www.apple.com/privacy/privacy-policy)