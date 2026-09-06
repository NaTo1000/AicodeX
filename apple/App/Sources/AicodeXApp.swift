import SwiftUI
import AicodeXCore

/// AicodeX — companion overlay code engine, rebuilt in SwiftUI.
@main
struct AicodeXApp: App {
    @StateObject private var model = AppViewModel()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(model)
                .frame(minWidth: 360, minHeight: 520)
        }
        #if os(macOS)
        .windowStyle(.hiddenTitleBar)
        .defaultSize(width: model.settings.window.width, height: model.settings.window.height)
        #endif

        #if os(macOS)
        Settings {
            SettingsView()
                .environmentObject(model)
        }
        #endif
    }
}
