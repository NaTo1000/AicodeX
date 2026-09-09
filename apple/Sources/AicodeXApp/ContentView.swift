#if canImport(SwiftUI)
import SwiftUI
import AicodeXCore

/// The HD overlay view for AicodeX — a clustered workspace where the watch,
/// phone, iPad, Mac, MacBook, MacBook Pro and AR glasses each run a distinct
/// function at the same time while staying connected through iCloud.
///
/// The app is a tabbed shell: every tab has its own SF Symbol icon, and the
/// Display tab renders a full-HD / 3D device panel (a spatial depth effect on
/// devices whose `DisplayProfile.supports3D` is true — MacBook Pro and AR
/// glasses).
struct ContentView: View {
    @StateObject private var cluster = ClusterStore()
    @State private var selection: AppTab = .cluster
    @State private var opacity: Double = 0.95
    @State private var spatial3D: Bool = true

    var body: some View {
        TabView(selection: $selection) {
            ClusterOverviewView(cluster: cluster)
                .tabItem { Label(AppTab.cluster.title, systemImage: AppTab.cluster.systemImage) }
                .tag(AppTab.cluster)

            DevicesView(cluster: cluster)
                .tabItem { Label(AppTab.devices.title, systemImage: AppTab.devices.systemImage) }
                .tag(AppTab.devices)

            DisplayView(cluster: cluster, spatial3D: $spatial3D)
                .tabItem { Label(AppTab.display.title, systemImage: AppTab.display.systemImage) }
                .tag(AppTab.display)

            SettingsView(opacity: $opacity, spatial3D: $spatial3D)
                .tabItem { Label(AppTab.settings.title, systemImage: AppTab.settings.systemImage) }
                .tag(AppTab.settings)
        }
        .opacity(opacity)
    }
}

// MARK: - Cluster tab

/// Cluster overview: connectivity + overall progress.
private struct ClusterOverviewView: View {
    @ObservedObject var cluster: ClusterStore

    var body: some View {
        NavigationStack {
            List {
                Section {
                    HStack {
                        Label("Cluster", systemImage: "point.3.connected.trianglepath.dotted")
                        Spacer()
                        Text("\(cluster.onlineCount)/\(ClusterDevice.Kind.allCases.count) online")
                            .foregroundStyle(.secondary)
                    }
                    HStack {
                        Label("iCloud", systemImage: "icloud")
                        Spacer()
                        Text(cluster.iCloudAvailable ? "Connected" : "Local only")
                            .foregroundStyle(cluster.iCloudAvailable ? .green : .orange)
                    }
                    VStack(alignment: .leading) {
                        Text("Overall progress")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        ProgressView(value: cluster.overallProgress)
                    }
                }
            }
            .navigationTitle("AicodeX")
        }
    }
}

// MARK: - Devices tab

/// One row per device, each doing a different function, with its icon.
private struct DevicesView: View {
    @ObservedObject var cluster: ClusterStore

    var body: some View {
        NavigationStack {
            List {
                Section("Devices — concurrent functions") {
                    ForEach(ClusterDevice.Kind.allCases) { kind in
                        DeviceRow(device: cluster.devices[kind]
                                  ?? ClusterDevice(kind: kind))
                    }
                }
            }
            .navigationTitle(AppTab.devices.title)
        }
    }
}

/// A single device's row: icon, distinct function, live progress, and status.
private struct DeviceRow: View {
    let device: ClusterDevice

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: device.kind.systemImage)
                .font(.title2)
                .frame(width: 32)
            VStack(alignment: .leading, spacing: 4) {
                Text(device.kind.rawValue.capitalized)
                    .font(.headline)
                Text(device.kind.function)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                ProgressView(value: device.progress)
            }
            Spacer()
            Circle()
                .fill(device.isOnline ? Color.green : Color.gray)
                .frame(width: 10, height: 10)
                .accessibilityLabel(device.isOnline ? "online" : "offline")
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Display tab (HD / 3D)

/// The HD / 3D display surface. Devices capable of spatial 3D (MacBook Pro,
/// AR glasses) render with a depth effect; others fall back to the HD card.
private struct DisplayView: View {
    @ObservedObject var cluster: ClusterStore
    @Binding var spatial3D: Bool

    var body: some View {
        NavigationStack {
            ScrollView {
                LazyVStack(spacing: 16) {
                    ForEach(ClusterDevice.Kind.allCases) { kind in
                        let device = cluster.devices[kind] ?? ClusterDevice(kind: kind)
                        DeviceDisplayCard(device: device, spatial3D: spatial3D)
                    }
                }
                .padding()
            }
            .navigationTitle(AppTab.display.title)
        }
    }
}

/// A full-HD / 3D display card for one device.
private struct DeviceDisplayCard: View {
    let device: ClusterDevice
    let spatial3D: Bool

    private var profile: DisplayProfile { device.kind.displayProfile }

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: device.kind.systemImage)
                    .font(.largeTitle)
                Spacer()
                Label(profile.hdLabel, systemImage: profile.supports3D
                      ? "cube.transparent" : "rectangle.fill")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Text(device.kind.rawValue.capitalized)
                .font(.title3).bold()
            Text(device.kind.function)
                .font(.caption)
                .foregroundStyle(.secondary)
            ProgressView(value: device.progress)
        }
        .padding()
        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 16))
        // Depth effect for the 3D-capable devices when spatial mode is on.
        .shadow(radius: profile.supports3D && spatial3D ? 12 : 4,
                x: 0, y: profile.supports3D && spatial3D ? 8 : 2)
        .rotation3DEffect(
            .degrees(profile.supports3D && spatial3D ? 8 : 0),
            axis: (x: 0, y: 1, z: 0))
        .scaleEffect(profile.supports3D && spatial3D ? 1.02 : 1.0)
        .animation(.easeInOut(duration: 0.3), value: spatial3D)
        .accessibilityElement(children: .combine)
    }
}

// MARK: - Settings tab

private struct SettingsView: View {
    @Binding var opacity: Double
    @Binding var spatial3D: Bool

    var body: some View {
        NavigationStack {
            List {
                Section("Overlay") {
                    HStack {
                        Label("Opacity", systemImage: "circle.lefthalf.filled")
                        Slider(value: $opacity, in: 0.2...1.0)
                    }
                }
                Section("Display") {
                    Toggle(isOn: $spatial3D) {
                        Label("Spatial 3D", systemImage: "cube.transparent")
                    }
                }
            }
            .navigationTitle(AppTab.settings.title)
        }
    }
}

#Preview {
    ContentView()
}
#endif
