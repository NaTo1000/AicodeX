import SwiftUI
import AicodeXCore

/// Root container with the Snippets / Actions / Settings tabs (parity with the Python overlay).
struct RootView: View {
    @EnvironmentObject private var model: AppViewModel

    var body: some View {
        TabView {
            SnippetsView()
                .tabItem { Label("Snippets", systemImage: "chevron.left.forwardslash.chevron.right") }
            ActionsView()
                .tabItem { Label("Actions", systemImage: "bolt") }
            SettingsView()
                .tabItem { Label("Settings", systemImage: "gear") }
        }
        .overlay(alignment: .bottom) {
            if let status = model.statusMessage {
                Text(status)
                    .font(.footnote)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(.thinMaterial, in: Capsule())
                    .padding(.bottom, 8)
                    .transition(.opacity)
                    .task(id: status) {
                        try? await Task.sleep(nanoseconds: 2_500_000_000)
                        if model.statusMessage == status { model.statusMessage = nil }
                    }
            }
        }
    }
}
