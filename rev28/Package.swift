// swift-tools-version: 6.3
import PackageDescription

let package = Package(
    name: "rev28",
    platforms: [
        .macOS("26.0")
    ],
    products: [
        .library(name: "Rev28Core", targets: ["Rev28Core"]),
        .executable(name: "rev28probe", targets: ["rev28probe"]),
    ],
    targets: [
        .target(
            name: "Rev28Core",
            path: "Sources/Rev28Core",
            swiftSettings: [.swiftLanguageMode(.v5)]
        ),
        .executableTarget(
            name: "rev28probe",
            dependencies: ["Rev28Core"],
            path: "Sources/rev28probe",
            swiftSettings: [.swiftLanguageMode(.v5)]
        ),
        .testTarget(
            name: "Rev28CoreTests",
            dependencies: ["Rev28Core"],
            path: "Tests/Rev28CoreTests",
            swiftSettings: [.swiftLanguageMode(.v5)]
        ),
    ]
)
