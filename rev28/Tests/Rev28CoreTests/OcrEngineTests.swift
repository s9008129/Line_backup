import AppKit
import CoreGraphics
import CoreText
import XCTest
@testable import Rev28Core

/// Renders its own synthetic fixtures (no screen content) for OCR tests.
enum TestImageFactory {
    static func image(text: String, fontSize: CGFloat = 120, padding: CGFloat = 60) -> CGImage? {
        let font = CTFontCreateWithName("PingFangTC-Medium" as CFString, fontSize, nil)
        let attributed = NSAttributedString(
            string: text,
            attributes: [
                .font: font,
                .foregroundColor: NSColor.black,
            ]
        )
        let line = CTLineCreateWithAttributedString(attributed)
        var ascent: CGFloat = 0
        var descent: CGFloat = 0
        var leading: CGFloat = 0
        let typographicWidth = CGFloat(CTLineGetTypographicBounds(line, &ascent, &descent, &leading))
        let width = Int(ceil(typographicWidth + padding * 2))
        let height = Int(ceil(ascent + descent + padding * 2))

        guard let colorSpace = CGColorSpace(name: CGColorSpace.sRGB),
              let context = CGContext(
                  data: nil,
                  width: width,
                  height: height,
                  bitsPerComponent: 8,
                  bytesPerRow: 0,
                  space: colorSpace,
                  bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
              ) else { return nil }

        context.setFillColor(CGColor(red: 1, green: 1, blue: 1, alpha: 1))
        context.fill(CGRect(x: 0, y: 0, width: width, height: height))
        context.textPosition = CGPoint(x: padding, y: padding + descent)
        CTLineDraw(line, context)
        return context.makeImage()
    }
}

final class OcrEngineTests: XCTestCase {
    private let engine = VisionOcrEngine()

    private func recognizedStrings(in text: String, fontSize: CGFloat = 120) async throws -> [String] {
        guard let image = TestImageFactory.image(text: text, fontSize: fontSize) else {
            throw XCTSkip("fixture rendering failed")
        }
        let items = try await engine.recognize(image: image)
        return items.map(\.text)
    }

    func testRecognizesMenuRowIdentity() async throws {
        let strings = try await recognizedStrings(in: "儲存全部")
        XCTAssertTrue(
            strings.contains(where: { OcrTextIdentity.isExactMatch($0, "儲存全部") }),
            "expected exact 儲存全部, got \(strings)"
        )
    }

    func testRecognizesCountIdentity() async throws {
        let strings = try await recognizedStrings(in: "57張照片")
        XCTAssertTrue(
            strings.contains(where: { OcrTextIdentity.isExactMatch($0, "57張照片") }),
            "expected exact 57張照片, got \(strings)"
        )
    }


    func testQuadIsInCapturePixelSpace() async throws {
    func testDiscriminatesZhenGlyphsInAlbumTitleContext() async throws {
        // 禎 (U+798E) vs 楨 (U+6968): exact matching, never normalized or merged.
        // The fixture uses the real album-title context (the production surface);
        // a bare single 楨 glyph is below Vision's text-detection granularity.
        let zhenText = "旻謙允禎成長日記"
        let zhenVariantText = "旻謙允楨成長日記"
        let zhen = try await recognizedStrings(in: zhenText, fontSize: 120)
        let zhenVariant = try await recognizedStrings(in: zhenVariantText, fontSize: 120)
        XCTAssertTrue(
            zhen.contains(where: { OcrTextIdentity.isExactMatch($0, zhenText) }),
            "expected exact \(zhenText), got \(zhen)"
        )
        XCTAssertFalse(
            zhen.contains(where: { OcrTextIdentity.isExactMatch($0, zhenVariantText) }),
            "禎 title must not read as the 楨 variant, got \(zhen)"
        )
        XCTAssertTrue(
            zhenVariant.contains(where: { OcrTextIdentity.isExactMatch($0, zhenVariantText) }),
            "expected exact \(zhenVariantText), got \(zhenVariant)"
        )
        XCTAssertFalse(
            zhenVariant.contains(where: { OcrTextIdentity.isExactMatch($0, zhenText) }),
            "楨 variant title must not read as 禎, got \(zhenVariant)"
        )
    }
        guard let image = TestImageFactory.image(text: "儲存全部", fontSize: 120) else {
            throw XCTSkip("fixture rendering failed")
        }
        let items = try await engine.recognize(image: image)
        guard let item = items.first(where: { OcrTextIdentity.isExactMatch($0.text, "儲存全部") }) else {
            return XCTFail("expected 儲存全部, got \(items.map(\.text))")
        }
        XCTAssertEqual(item.quadCapturePx.count, 4)
        XCTAssertGreaterThan(item.boundingBoxCapturePx.width, 0)
        XCTAssertGreaterThan(item.boundingBoxCapturePx.height, 0)
        XCTAssertLessThanOrEqual(item.boundingBoxCapturePx.maxX, CGFloat(image.width) + 1.0)
        XCTAssertLessThanOrEqual(item.boundingBoxCapturePx.maxY, CGFloat(image.height) + 1.0)
        XCTAssertGreaterThan(item.confidence, 0.0)
    }
}
