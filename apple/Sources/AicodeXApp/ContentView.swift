import SwiftUI

/// The main overlay view for AicodeX — a hotkey-driven, customizable panel.
struct ContentView: View {
    @State private var opacity: Double = 0.95

    var body: some View {
        NavigationStack {
            List {
                Section("Snippets") {
                    Label("Browse code snippets", systemImage: "doc.on.doc")
                    Label("Quick copy", systemImage: "paperclip")
                }
                Section("Actions") {
                    Label("Format code", systemImage: "wand.and.stars")
                    Label("Generate docstring", systemImage: "text.quote")
                }
                Section("Settings") {
                    HStack {
                        Label("Opacity", systemImage: "circle.lefthalf.filled")
                        Slider(value: $opacity, in: 0.2...1.0)
                    }
                    Label("Hotkeys", systemImage: "keyboard")
                }
            }
            .navigationTitle("AicodeX")
        }
        .opacity(opacity)
    }
}

#Preview {
    ContentView()
}
