// swift-tools-version:5.9
//
// AicodeX — SwiftUI app package for Xcode.
// Open this file in Xcode (File ▸ Open ▸ Package.swift) or build with
// `swift build`. Apple credentials are provided via the environment / CI —
// see APPLE_CREDENTIALS.md.

import PackageDescription

let package = Package(
    name: "AicodeX",
    platforms: [
        .iOS(.v16),
        .macOS(.v13)
    ],
    products: [
        .library(name: "AicodeXApp", targets: ["AicodeXApp"])
    ],
    targets: [
        .target(
            name: "AicodeXApp",
            path: "Sources/AicodeXApp"
        ),
        .testTarget(
            name: "AicodeXAppTests",
            dependencies: ["AicodeXApp"],
            path: "Tests/AicodeXAppTests"
        )
    ]
)
