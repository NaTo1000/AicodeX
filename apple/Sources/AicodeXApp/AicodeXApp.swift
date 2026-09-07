#if canImport(SwiftUI)
import SwiftUI

/// AicodeX app entry point — the hotkey-enabled companion overlay.
@main
struct AicodeXApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
        #if os(macOS)
        .windowStyle(.hiddenTitleBar)
        #endif
    }
}
#else
// Cross-platform fallback entry point (Linux CI / non-Apple toolchains without
// SwiftUI). The full SwiftUI app is built on Apple platforms.
import AicodeXCore

@main
enum AicodeXAppCLI {
    static func main() {
        let devices = ClusterDevice.Kind.allCases
        let online = devices.count
        print("AicodeX clustered workspace — \(online) devices: " +
              devices.map(\.rawValue).joined(separator: ", "))
    }
}
#endif
