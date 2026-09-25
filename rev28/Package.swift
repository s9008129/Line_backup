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
        .executable(name: "rev28harness", targets: ["rev28harness"]),
        .executable(name: "rev28occluder", targets: ["rev28occluder"]),
        .executable(name: "rev28ctl", targets: ["rev28ctl"]),
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
        .executableTarget(
            name: "rev28harness",
            dependencies: ["Rev28Core"],
            path: "Sources/rev28harness",
            swiftSettings: [.swiftLanguageMode(.v5)]
        ),
        .executableTarget(
            name: "rev28occluder",
            dependencies: ["Rev28Core"],
            path: "Sources/rev28occluder",
            swiftSettings: [.swiftLanguageMode(.v5)]
        ),
        .executableTarget(
            name: "rev28ctl",
            dependencies: ["Rev28Core"],
            path: "Sources/rev28ctl",
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
