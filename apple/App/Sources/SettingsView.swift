import SwiftUI
import AicodeXCore

struct SettingsView: View {
    @EnvironmentObject private var model: AppViewModel

    var body: some View {
        Form {
            Section("Overlay") {
                HStack {
                    Text("Opacity")
                    Slider(
                        value: Binding(
                            get: { model.settings.window.opacity },
                            set: { model.setOpacity($0) }
                        ),
                        in: 0.5...1.0,
                        step: 0.01
                    )
                    Text(model.settings.window.opacity, format: .percent.precision(.fractionLength(0)))
                        .frame(width: 52, alignment: .trailing)
                        .monospacedDigit()
                }
                #if os(macOS)
                Toggle("Overlay visible", isOn: Binding(
                    get: { model.overlayVisible },
                    set: { _ in model.toggleOverlay() }
                ))
                #endif
            }

            Section("Hotkeys") {
                ForEach(model.settings.hotkeys) { hotkey in
                    HStack {
                        Text(hotkey.displayName)
                        Spacer()
                        Text(hotkey.keyCombo)
                            .font(.system(.body, design: .monospaced))
                            .foregroundStyle(.secondary)
                    }
                }
            }

            Section("Features") {
                featureToggle("HandBrake Integration", \.features.handbrakeIntegration)
                featureToggle("Auto Format", \.features.autoFormat)
                featureToggle("Snippet Suggestions", \.features.snippetSuggestions)
            }

            Section("About") {
                LabeledContent("Version", value: "1.0.0")
                LabeledContent("Bundle", value: Bundle.main.bundleIdentifier ?? "—")
            }
        }
        .navigationTitle("Settings")
    }

    private func featureToggle(_ title: String, _ keyPath: WritableKeyPath<AppSettings, Bool>) -> some View {
        Toggle(title, isOn: Binding(
            get: { model.settings[keyPath: keyPath] },
            set: { newValue in
                model.settings[keyPath: keyPath] = newValue
                model.persist()
            }
        ))
    }
}
