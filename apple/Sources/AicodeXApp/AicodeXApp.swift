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
