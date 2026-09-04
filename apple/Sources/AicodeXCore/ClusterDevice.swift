import Foundation

/// A device participating in the AicodeX clustered workspace.
///
/// Each Apple device runs a *different* function at the same time while
/// staying connected through the shared iCloud key-value store.
struct ClusterDevice: Identifiable, Codable, Equatable {
    enum Kind: String, Codable, CaseIterable {
        case watch
        case phone
        case iPad
        case mac

        /// The distinct function this device performs in the cluster.
        var function: String {
            switch self {
            case .watch: return "Quick actions & glanceable status"
            case .phone: return "Capture, review & approve on the go"
            case .iPad:  return "Sketch, annotate & pair editing"
            case .mac:   return "Heavy builds, orchestration & analysis"
            }
        }

        var systemImage: String {
            switch self {
            case .watch: return "applewatch"
            case .phone: return "iphone"
            case .iPad:  return "ipad"
            case .mac:   return "macbook"
            }
        }
    }

    var id: Kind { kind }
    let kind: Kind
    var isOnline: Bool
    var progress: Double       // 0...1 for the device's current function
    var lastUpdate: Date

    init(kind: Kind, isOnline: Bool = false, progress: Double = 0,
         lastUpdate: Date = Date()) {
        self.kind = kind
        self.isOnline = isOnline
        self.progress = progress
        self.lastUpdate = lastUpdate
    }
}
