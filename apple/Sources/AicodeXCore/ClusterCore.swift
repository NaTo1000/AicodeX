import Foundation

/// Pure, platform-independent cluster state and coordination logic.
///
/// This enum contains the parts of the clustered workspace that do **not**
/// depend on SwiftUI, Combine, or Apple frameworks, so they compile and are
/// unit-testable with `swift test` on any platform (including Linux CI).
/// The SwiftUI `ClusterStore` wraps this logic and adds iCloud persistence.
enum ClusterCore {

    /// Clamp a device progress value into the inclusive range 0...1.
    static func clampedProgress(_ value: Double) -> Double {
        min(max(value, 0), 1)
    }

    /// Aggregate progress across the whole clustered workspace.
    static func overallProgress<S: Sequence>(of devices: S) -> Double
    where S.Element == ClusterDevice {
        let all = Array(devices)
        guard !all.isEmpty else { return 0 }
        return all.reduce(0) { $0 + $1.progress } / Double(all.count)
    }

    /// Number of devices currently online.
    static func onlineCount<S: Sequence>(of devices: S) -> Int
    where S.Element == ClusterDevice {
        devices.filter(\.isOnline).count
    }

    /// The iCloud key used to persist a device's state.
    static func storageKey(for kind: ClusterDevice.Kind) -> String {
        "aicodex.cluster.\(kind.rawValue)"
    }

    /// Apply a progress update to a device, returning the updated copy.
    static func applyingProgress(_ progress: Double, to device: ClusterDevice,
                                 at date: Date = Date()) -> ClusterDevice {
        var updated = device
        updated.progress = clampedProgress(progress)
        updated.isOnline = true
        updated.lastUpdate = date
        return updated
    }
}
