import Foundation

/// Pure, platform-independent cluster state and coordination logic.
///
/// This enum contains the parts of the clustered workspace that do **not**
/// depend on SwiftUI, Combine, or Apple frameworks, so they compile and are
/// unit-testable with `swift test` on any platform (including Linux CI).
/// The SwiftUI `ClusterStore` wraps this logic and adds iCloud persistence.
public enum ClusterCore {

    /// Clamp a device progress value into the inclusive range 0...1.
    public static func clampedProgress(_ value: Double) -> Double {
        min(max(value, 0), 1)
    }

    /// Aggregate progress across the whole clustered workspace.
    public static func overallProgress<S: Sequence>(of devices: S) -> Double
    where S.Element == ClusterDevice {
        let all = Array(devices)
        guard !all.isEmpty else { return 0 }
        return all.reduce(0) { $0 + $1.progress } / Double(all.count)
    }

    /// Number of devices currently online.
    public static func onlineCount<S: Sequence>(of devices: S) -> Int
    where S.Element == ClusterDevice {
        devices.filter(\.isOnline).count
    }

    /// The iCloud key used to persist a device's state.
    public static func storageKey(for kind: ClusterDevice.Kind) -> String {
        "aicodex.cluster.\(kind.rawValue)"
    }

    /// Apply a progress update to a device, returning the updated copy.
    public static func applyingProgress(_ progress: Double, to device: ClusterDevice,
                                        at date: Date = Date()) -> ClusterDevice {
        var updated = device
        updated.progress = clampedProgress(progress)
        updated.isOnline = true
        updated.lastUpdate = date
        return updated
    }
}

/// The top-level tabs of the SwiftUI app, each with its own SF Symbol icon.
///
/// Pure value type (no SwiftUI dependency) so it compiles and is testable on
/// any platform; the SwiftUI shell turns these into `TabView` items.
public enum AppTab: String, Codable, CaseIterable, Identifiable {
    case cluster
    case devices
    case display
    case settings

    public var id: String { rawValue }

    /// The tab's display title.
    public var title: String {
        switch self {
        case .cluster:  return "Cluster"
        case .devices:  return "Devices"
        case .display:  return "Display"
        case .settings: return "Settings"
        }
    }

    /// The tab's SF Symbol icon.
    public var systemImage: String {
        switch self {
        case .cluster:  return "point.3.connected.trianglepath.dotted"
        case .devices:  return "rectangle.on.rectangle.angled"
        case .display:  return "rectangle.3.group.fill"
        case .settings: return "gearshape.fill"
        }
    }
}
