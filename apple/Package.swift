// swift-tools-version:5.9
//
// AicodeX — Swift package.
//
// `AicodeXCore` is the platform-independent clustered-workspace logic and
// builds + tests on any platform (`swift build` / `swift test`), including
// Linux CI. The SwiftUI app UI lives in `App/` and is imported into Xcode
// (it requires the Apple SDK / SwiftUI). See APPLE_CREDENTIALS.md.

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
        .library(name: "AicodeXCore", targets: ["AicodeXCore"])
    ],
    targets: [
        .target(
            name: "AicodeXCore",
            path: "Sources/AicodeXCore"
        ),
        .testTarget(
            name: "AicodeXAppTests",
            dependencies: ["AicodeXCore"],
            path: "Tests/AicodeXAppTests"
        )
    ]
)
