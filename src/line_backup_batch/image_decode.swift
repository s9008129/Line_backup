import Foundation
import ImageIO
import CoreGraphics
import CryptoKit
import Darwin

// Explicit read-only image directory/count. Full RGB draw, not header-only decode.
guard CommandLine.arguments.count == 3,
      let expected = Int(CommandLine.arguments[2]), expected > 0 else { exit(2) }
let root = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
guard root.standardizedFileURL.path == root.path,
      root.resolvingSymlinksInPath().path == root.path else { exit(2) }
do {
    let names = try FileManager.default.contentsOfDirectory(atPath: root.path).sorted()
    var results: [[String: Any]] = []
    for name in names {
        let url = root.appendingPathComponent(name)
        var item: [String: Any] = ["name": name, "decoded": false]
        let fd = open(url.path, O_RDONLY | O_NOFOLLOW | O_NONBLOCK)
        if fd >= 0 {
            defer { close(fd) }
            var info = stat()
            if fstat(fd, &info) == 0, (info.st_mode & S_IFMT) == S_IFREG,
               info.st_size > 0, info.st_size < 512 * 1024 * 1024 {
                var data = Data(); var buffer = [UInt8](repeating: 0, count: 65536)
                var readOK = true
                while true {
                    let length = read(fd, &buffer, buffer.count)
                    if length == 0 { break }
                    if length < 0 { readOK = false; break }
                    data.append(contentsOf: buffer.prefix(length))
                    if data.count > 512 * 1024 * 1024 { readOK = false; break }
                }
                var after = stat()
                let stable = fstat(fd, &after) == 0 && after.st_dev == info.st_dev && after.st_ino == info.st_ino
                    && after.st_size == info.st_size && after.st_mtimespec.tv_sec == info.st_mtimespec.tv_sec
                    && after.st_mtimespec.tv_nsec == info.st_mtimespec.tv_nsec
                    && after.st_ctimespec.tv_sec == info.st_ctimespec.tv_sec && after.st_ctimespec.tv_nsec == info.st_ctimespec.tv_nsec
                if readOK && stable && data.count == info.st_size,
                   let source = CGImageSourceCreateWithData(data as CFData, nil),
                   CGImageSourceGetCount(source) == 1,
                   let image = CGImageSourceCreateImageAtIndex(source, 0,
                        [kCGImageSourceShouldCache: true, kCGImageSourceShouldCacheImmediately: true] as CFDictionary),
                   CGImageSourceGetStatusAtIndex(source, 0) == .statusComplete,
                   image.width > 0, image.height > 0, image.width <= 32768, image.height <= 32768,
                   image.width * image.height <= 50_000_000,
                   let context = CGContext(data: nil, width: image.width, height: image.height,
                        bitsPerComponent: 8, bytesPerRow: 0, space: CGColorSpaceCreateDeviceRGB(),
                        bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue) {
                    context.draw(image, in: CGRect(x: 0, y: 0, width: image.width, height: image.height))
                    item["decoded"] = context.makeImage() != nil
                    item["width"] = image.width; item["height"] = image.height
                    item["sha256"] = SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
                    item["contentType"] = CGImageSourceGetType(source) as String? ?? "UNKNOWN"
                }
            }
        }
        results.append(item)
    }
    let passed = results.count == expected && results.allSatisfy { $0["decoded"] as? Bool == true }
    let output: [String: Any] = ["verdict": passed ? "PASS" : "FAIL", "expected": expected,
        "actualEntries": names.count, "decoder": "macOS ImageIO plus full RGB bitmap draw",
        "destination": root.path, "entries": results, "readOnly": true]
    FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject: output, options: [.prettyPrinted, .sortedKeys]))
    FileHandle.standardOutput.write(Data("\n".utf8)); exit(passed ? 0 : 1)
} catch {
    FileHandle.standardError.write(Data("read-only decode failed: \(error)\n".utf8));exit(2)
}
