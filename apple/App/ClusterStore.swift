import Foundation
import Combine
import AicodeXCore

/// Connectivity + shared state for the AicodeX clustered workspace.
///
/// Devices (watch, phone, iPad, Mac) each run a distinct function
/// concurrently while staying in sync through the iCloud key-value store
/// (`NSUbiquitousKeyValueStore`). State transitions are delegated to the
/// platform-independent `ClusterCore`; this type adds iCloud persistence and
/// `@Published` connectivity for the SwiftUI views. When iCloud is
/// unavailable the store keeps an in-memory copy so the cluster keeps working
/// and syncs when connectivity returns.
final class ClusterStore: ObservableObject {
    /// Published device states, keyed by device kind.
    @Published private(set) var devices: [ClusterDevice.Kind: ClusterDevice]

    /// Whether the iCloud ubiquitous store is reachable.
    @Published private(set) var iCloudAvailable: Bool

    private let ubiquitous = NSUbiquitousKeyValueStore.default
    private var cancellables: Set<AnyCancellable> = []

    init(devices: [ClusterDevice]? = nil) {
        let initial = devices ?? ClusterDevice.Kind.allCases.map {
            ClusterDevice(kind: $0, isOnline: true, progress: 0)
        }
        self.devices = Dictionary(uniqueKeysWithValues: initial.map { ($0.kind, $0) })
        self.iCloudAvailable = FileManager.default.ubiquityIdentityToken != nil

        NotificationCenter.default
            .publisher(for: NSUbiquitousKeyValueStore.didChangeExternallyNotification)
            .sink { [weak self] _ in self?.pullFromiCloud() }
            .store(in: &cancellables)
        ubiquitous.synchronize()
    }

    // MARK: - Cluster operations

    /// Advance a device's function progress and push the update to iCloud so
    /// the rest of the cluster sees it in realtime.
    func updateProgress(for kind: ClusterDevice.Kind, to progress: Double) {
        let current = devices[kind] ?? ClusterDevice(kind: kind, isOnline: true)
        let updated = ClusterCore.applyingProgress(progress, to: current)
        devices[kind] = updated
        pushToiCloud(updated)
    }

    func setOnline(_ online: Bool, for kind: ClusterDevice.Kind) {
        var device = devices[kind] ?? ClusterDevice(kind: kind)
        device.isOnline = online
        devices[kind] = device
        pushToiCloud(device)
    }

    /// Aggregate progress across the whole clustered workspace.
    var overallProgress: Double {
        ClusterCore.overallProgress(of: devices.values)
    }

    var onlineCount: Int {
        ClusterCore.onlineCount(of: devices.values)
    }

    // MARK: - iCloud sync

    private func pushToiCloud(_ device: ClusterDevice) {
        guard let data = try? JSONEncoder().encode(device) else { return }
        ubiquitous.set(data, forKey: ClusterCore.storageKey(for: device.kind))
        ubiquitous.synchronize()
    }

    private func pullFromiCloud() {
        for kind in ClusterDevice.Kind.allCases {
            guard let data = ubiquitous.data(forKey: ClusterCore.storageKey(for: kind)),
                  let device = try? JSONDecoder().decode(ClusterDevice.self, from: data)
            else { continue }
            devices[kind] = device
        }
    }
}
