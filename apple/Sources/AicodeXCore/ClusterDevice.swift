import Foundation

/// A device participating in the AicodeX clustered workspace.
///
/// Each Apple device runs a *different* function at the same time while
/// staying connected through the shared iCloud key-value store.
public struct ClusterDevice: Identifiable, Codable, Equatable {
    public enum Kind: String, Codable, CaseIterable {
        case watch
        case phone
        case iPad
        case mac
        case macBook
        case macBookPro
        case arGlasses

        /// The distinct function this device performs in the cluster.
        public var function: String {
            switch self {
            case .watch:      return "Quick actions & glanceable status"
            case .phone:      return "Capture, review & approve on the go"
            case .iPad:       return "Sketch, annotate & pair editing"
            case .mac:        return "Heavy builds, orchestration & analysis"
            case .macBook:    return "Mobile orchestration & review"
            case .macBookPro: return "Full builds, rendering & deep analysis"
            case .arGlasses:  return "Spatial overlay & heads-up display"
            }
        }

        /// SF Symbol for the device (its icon in the UI).
        public var systemImage: String {
            switch self {
            case .watch:      return "applewatch"
            case .phone:      return "iphone"
            case .iPad:       return "ipad"
            case .mac:        return "macbook"
            case .macBook:    return "macbook.gen1"
            case .macBookPro: return "macbook.gen2"
            case .arGlasses:  return "visionpro"
            }
        }

        /// The display profile (HD / 3D capability) for this device kind.
        public var displayProfile: DisplayProfile {
            DisplayProfile(for: self)
        }
    }

    public var id: Kind { kind }
    public let kind: Kind
    public var isOnline: Bool
    public var progress: Double       // 0...1 for the device's current function
    public var lastUpdate: Date

    public init(kind: Kind, isOnline: Bool = false, progress: Double = 0,
                lastUpdate: Date = Date()) {
        self.kind = kind
        self.isOnline = isOnline
        self.progress = progress
        self.lastUpdate = lastUpdate
    }
}

/// The display capability of a device kind — HD resolution and, where the
/// hardware supports it, a 3D / spatial (depth) presentation.
public struct DisplayProfile: Codable, Equatable {
    public enum Rendering: String, Codable, CaseIterable {
        case standard2D = "2d"
        case spatial3D = "3d"
    }

    /// Human-readable HD label (e.g. "HD", "Full HD", "4K HDR", "Spatial").
    public let hdLabel: String
    /// Whether the device presents a full HD surface.
    public let isHD: Bool
    /// Whether the device supports the 3D / spatial rendering path.
    public let supports3D: Bool
    /// Preferred rendering path for the device.
    public let rendering: Rendering

    public init(hdLabel: String, isHD: Bool, supports3D: Bool,
                rendering: Rendering) {
        self.hdLabel = hdLabel
        self.isHD = isHD
        self.supports3D = supports3D
        self.rendering = rendering
    }

    /// The display profile for a given device kind.
    public init(for kind: ClusterDevice.Kind) {
        switch kind {
        case .watch:
            self.init(hdLabel: "HD", isHD: true, supports3D: false,
                      rendering: .standard2D)
        case .phone:
            self.init(hdLabel: "Full HD", isHD: true, supports3D: false,
                      rendering: .standard2D)
        case .iPad:
            self.init(hdLabel: "Liquid Retina HD", isHD: true, supports3D: false,
                      rendering: .standard2D)
        case .mac:
            self.init(hdLabel: "Retina HD", isHD: true, supports3D: false,
                      rendering: .standard2D)
        case .macBook:
            self.init(hdLabel: "Retina HD", isHD: true, supports3D: false,
                      rendering: .standard2D)
        case .macBookPro:
            self.init(hdLabel: "Liquid Retina XDR", isHD: true, supports3D: true,
                      rendering: .spatial3D)
        case .arGlasses:
            self.init(hdLabel: "Spatial 3D", isHD: true, supports3D: true,
                      rendering: .spatial3D)
        }
    }
}
