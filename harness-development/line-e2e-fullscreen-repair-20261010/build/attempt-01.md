# Build attempt 01

- Outcome: FAIL; compile only, no execution or UI input.
- Toolchain: Xcode 26.6, Swift 6.3.3, explicit macOS26.5 SDK.
- `FullscreenCapture.swift`: Swift could not infer `.png` from ScreenCaptureKit's imported `UTTypeReference` property type.
- `VisionRegions.swift`: the Vision `ImageRequestHandler` initializer in this SDK does not accept an `options` argument.
- Learning: use the explicitly qualified `UTType.png` value and the SDK's `ImageRequestHandler(_ image:orientation:)` initializer. Both failures are source/API binding issues; this attempt established no runtime capture or OCR result.
