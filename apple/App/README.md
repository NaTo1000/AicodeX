# AicodeXApp — SwiftUI App Sources

These SwiftUI sources are the AicodeX app UI. They require the **Apple SDK /
SwiftUI**, so they are **not** part of the cross-platform `swift build` target
(which Linux CI runs); the platform-independent logic lives in
`../Sources/AicodeXCore` and is unit-tested there.

## Building with Xcode

1. Open `../Package.swift` in Xcode (File ▸ Open) to get the `AicodeXCore`
   library, **or** add `../` as a local Swift package dependency.
2. Create an **App** target (iOS + macOS + watchOS) and add the files in this
   `App/` group to it, linking `AicodeXCore`.
3. Enable the **iCloud ▸ Key-Value Storage** capability for the clustered
   workspace sync.
4. Provide Apple credentials via the environment / CI — see
   `../APPLE_CREDENTIALS.md` (nothing is committed).

## Files

- `AicodeXApp.swift` — `@main` app entry point.
- `ContentView.swift` — the HD clustered-workspace overlay (watch/phone/iPad/
  Mac rows, live progress, iCloud status).
- `ClusterStore.swift` — `ObservableObject` bridging `AicodeXCore` logic with
  the iCloud key-value store and SwiftUI connectivity.
