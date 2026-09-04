import SwiftUI
import AicodeXCore

/// The HD overlay view for AicodeX — a clustered workspace where the watch,
/// phone, iPad and Mac each run a distinct function at the same time while
/// staying connected through iCloud.
struct ContentView: View {
    @StateObject private var cluster = ClusterStore()
    @State private var opacity: Double = 0.95

    var body: some View {
        NavigationStack {
            List {
                // Cluster overview: connectivity + overall progress.
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

                // One row per device, each doing a different function.
                Section("Devices — concurrent functions") {
                    ForEach(ClusterDevice.Kind.allCases) { kind in
                        DeviceRow(device: cluster.devices[kind]
                                  ?? ClusterDevice(kind: kind))
                    }
                }

                Section("Overlay") {
                    HStack {
                        Label("Opacity", systemImage: "circle.lefthalf.filled")
                        Slider(value: $opacity, in: 0.2...1.0)
                    }
                }
            }
            .navigationTitle("AicodeX")
        }
        .opacity(opacity)
    }
}

/// A single device's row: its distinct function, live progress, and status.
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

#Preview {
    ContentView()
}
