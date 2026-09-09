import XCTest
@testable import AicodeXCore

/// Tests for the platform-independent cluster logic. These run with
/// `swift test` on any platform (including Linux CI) because `AicodeXCore`
/// has no SwiftUI/Apple-framework dependencies.
final class ClusterCoreTests: XCTestCase {

    func testAllDeviceKindsCovered() {
        XCTAssertEqual(Set(ClusterDevice.Kind.allCases),
                       [.watch, .phone, .iPad, .mac,
                        .macBook, .macBookPro, .arGlasses])
    }

    func testEachDeviceHasDistinctFunction() {
        let functions = ClusterDevice.Kind.allCases.map(\.function)
        XCTAssertEqual(functions.count, Set(functions).count,
                       "each device should perform a distinct function")
    }

    func testEachDeviceHasDistinctIcon() {
        let icons = ClusterDevice.Kind.allCases.map(\.systemImage)
        XCTAssertEqual(icons.count, Set(icons).count,
                       "each device should have a distinct SF Symbol icon")
    }

    func testProgressClamping() {
        XCTAssertEqual(ClusterCore.clampedProgress(-0.5), 0)
        XCTAssertEqual(ClusterCore.clampedProgress(0.5), 0.5)
        XCTAssertEqual(ClusterCore.clampedProgress(1.7), 1)
    }

    func testApplyingProgressMarksOnlineAndClamps() {
        let device = ClusterDevice(kind: .mac, isOnline: false)
        let updated = ClusterCore.applyingProgress(1.4, to: device)
        XCTAssertEqual(updated.progress, 1)
        XCTAssertTrue(updated.isOnline)
    }

    func testOverallProgress() {
        let devices = [
            ClusterDevice(kind: .mac, isOnline: true, progress: 1.0),
            ClusterDevice(kind: .phone, isOnline: true, progress: 0.5),
        ]
        XCTAssertEqual(ClusterCore.overallProgress(of: devices), 0.75, accuracy: 1e-9)
        XCTAssertEqual(ClusterCore.onlineCount(of: devices), 2)
    }

    func testStorageKey() {
        XCTAssertEqual(ClusterCore.storageKey(for: .mac), "aicodex.cluster.mac")
    }

    func testDeviceCodableRoundTrip() throws {
        let device = ClusterDevice(kind: .iPad, isOnline: true, progress: 0.3)
        let data = try JSONEncoder().encode(device)
        let decoded = try JSONDecoder().decode(ClusterDevice.self, from: data)
        XCTAssertEqual(decoded.kind, .iPad)
        XCTAssertEqual(decoded.progress, 0.3, accuracy: 1e-9)
    }

    // MARK: - App tabs

    func testAllTabsPresent() {
        XCTAssertEqual(Set(AppTab.allCases),
                       [.cluster, .devices, .display, .settings])
    }

    func testEachTabHasIconAndTitle() {
        for tab in AppTab.allCases {
            XCTAssertFalse(tab.systemImage.isEmpty,
                           "\(tab) must have an SF Symbol icon")
            XCTAssertFalse(tab.title.isEmpty,
                           "\(tab) must have a title")
        }
    }

    func testEachTabHasDistinctIcon() {
        let icons = AppTab.allCases.map(\.systemImage)
        XCTAssertEqual(icons.count, Set(icons).count,
                       "each tab should have a distinct icon")
    }

    // MARK: - Display profiles (HD / 3D)

    func testEveryDeviceIsHD() {
        for kind in ClusterDevice.Kind.allCases {
            XCTAssertTrue(kind.displayProfile.isHD,
                          "\(kind) should present a full-HD surface")
            XCTAssertFalse(kind.displayProfile.hdLabel.isEmpty)
        }
    }

    func testThreeDCapableDevices() {
        let threeD = ClusterDevice.Kind.allCases.filter(\.displayProfile.supports3D)
        XCTAssertEqual(Set(threeD), [.macBookPro, .arGlasses],
                       "MacBook Pro and AR glasses support spatial 3D")
        for kind in threeD {
            XCTAssertEqual(kind.displayProfile.rendering, .spatial3D)
        }
    }

    func testNon3DDevicesRender2D() {
        for kind in [ClusterDevice.Kind.watch, .phone, .iPad, .mac, .macBook] {
            XCTAssertFalse(kind.displayProfile.supports3D)
            XCTAssertEqual(kind.displayProfile.rendering, .standard2D)
        }
    }
}
