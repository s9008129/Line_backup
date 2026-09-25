import CoreGraphics
import Foundation
import Rev28Core
import ScreenCaptureKit

// Raw ScreenCaptureKit capture used by the calibration driver (same call path as
// the W1 capture service) plus a pixel probe that measures the capture origin
// directly from image content instead of trusting the window frame.

enum RawCapture {
    static func capture(window: SCWindow, configuration: CaptureConfiguration) async throws -> CGImage {
        let filter = SCContentFilter(desktopIndependentWindow: window)
        let config = SCScreenshotConfiguration()
        config.includeChildWindows = configuration.includeChildWindows
        config.ignoreShadows = configuration.ignoreShadows
        config.ignoreClipping = configuration.ignoreClipping
        config.showsCursor = configuration.showsCursor
        if let sourceRect = configuration.sourceRect {
            config.sourceRect = sourceRect
        }
        let output = try await SCScreenshotManager.captureScreenshot(contentFilter: filter, configuration: config)
        guard let image = output.sdrImage else {
            throw NSError(domain: "rev28ctl", code: 3, userInfo: [NSLocalizedDescriptionKey: "raw capture produced no image"])
        }
        return image
    }
}

enum PixelProbe {
    /// Finds the top-left-most strongly red pixel (the harness origin marker).
    static func findRedSquareTopLeft(in image: CGImage, minRed: Int = 140, maxOther: Int = 110) -> CGPoint? {
        let width = image.width
        let height = image.height
        let bytesPerRow = width * 4
        var buffer = [UInt8](repeating: 0, count: bytesPerRow * height)
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        guard let context = CGContext(
            data: &buffer,
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: bytesPerRow,
            space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
        ) else {
            return nil
        }
        context.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
        for row in 0..<height {
            for column in 0..<width {
                let offset = row * bytesPerRow + column * 4
                let r = Int(buffer[offset])
                let g = Int(buffer[offset + 1])
                let b = Int(buffer[offset + 2])
                if r >= minRed, g <= maxOther, b <= maxOther {
                    return CGPoint(x: column, y: row)
                }
            }
        }
        return nil
    }
}
