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
        .executable(name: "rev28replay", targets: ["rev28replay"]),
        .library(name: "Rev28NativeFeasibility", targets: ["Rev28NativeFeasibility"]),
        .executable(name: "rev28nativefeasibility", targets: ["rev28nativefeasibility"]),
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
        .executableTarget(
            name: "rev28replay",
            dependencies: ["Rev28Core"],
            path: "Sources/rev28replay",
            swiftSettings: [.swiftLanguageMode(.v5)]
        ),
        .target(
            name: "Rev28NativeFeasibility",
            path: "Sources/Rev28NativeFeasibility",
            sources: ["NativePreDownContract.swift"],
            swiftSettings: [.swiftLanguageMode(.v5)]
        ),
        .executableTarget(
            name: "rev28nativefeasibility",
            dependencies: ["Rev28NativeFeasibility"],
            path: "Sources/rev28nativefeasibility",
            sources: ["main.swift"],
            swiftSettings: [.swiftLanguageMode(.v5)]
        ),
        .testTarget(
            name: "Rev28CoreTests",
            dependencies: ["Rev28Core"],
            path: "Tests/Rev28CoreTests",
            swiftSettings: [.swiftLanguageMode(.v5)]
        ),
        .testTarget(
            name: "Rev28NativeFeasibilityTests",
            dependencies: ["Rev28NativeFeasibility"],
            path: "Tests/Rev28NativeFeasibilityTests",
            swiftSettings: [.swiftLanguageMode(.v5)]
        ),
    ]
)
