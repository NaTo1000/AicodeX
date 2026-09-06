// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "AicodeX",
    platforms: [
        .iOS(.v16),
        .macOS(.v13)
    ],
    products: [
        // Pure-Foundation core: compiles and tests on Linux (`swift test`).
        .library(name: "AicodeXCore", targets: ["AicodeXCore"])
    ],
    targets: [
        .target(
            name: "AicodeXCore",
            path: "Sources/AicodeXCore"
        ),
        // The SwiftUI app (apple/App) is built by Xcode on macOS only and is
        // intentionally NOT part of this package so `swift build`/`swift test` work on Linux.
        .testTarget(
            name: "AicodeXCoreTests",
            dependencies: ["AicodeXCore"],
            path: "Tests/AicodeXCoreTests"
        )
    ]
)
