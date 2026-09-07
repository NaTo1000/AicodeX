// swift-tools-version:5.9
//
// AicodeX — Swift package.
//
// `AicodeXCore` is the platform-independent clustered-workspace logic and
// builds + tests on any platform (`swift build` / `swift test`), including
// Linux CI. `AicodeXApp` is the SwiftUI app target; its sources use conditional
// compilation (`#if canImport(SwiftUI)` / `#if canImport(Combine)`) so the
// package builds cross-platform while the full SwiftUI UI is compiled on Apple
// platforms (and via Xcode for the App Store). See APPLE_CREDENTIALS.md.

import PackageDescription

let package = Package(
    name: "AicodeX",
    platforms: [
        .iOS(.v16),
        .macOS(.v13),
        .watchOS(.v9)
    ],
    products: [
        // Platform-independent cluster logic — builds and tests everywhere.
        .library(name: "AicodeXCore", targets: ["AicodeXCore"]),
        // The SwiftUI app — builds everywhere via conditional compilation; the
        // full UI is active on Apple platforms.
        .executable(name: "AicodeXApp", targets: ["AicodeXApp"])
    ],
    targets: [
        .target(
            name: "AicodeXCore",
            path: "Sources/AicodeXCore"
        ),
        .executableTarget(
            name: "AicodeXApp",
            dependencies: ["AicodeXCore"],
            path: "Sources/AicodeXApp"
        ),
        .testTarget(
            name: "AicodeXAppTests",
            dependencies: ["AicodeXCore", "AicodeXApp"],
            path: "Tests/AicodeXAppTests"
        )
    ]
)
