import XCTest
@testable import AicodeXCore

/// Tests for the platform-independent cluster logic. These run with
/// `swift test` on any platform (including Linux CI) because `AicodeXCore`
/// has no SwiftUI/Apple-framework dependencies.
final class ClusterCoreTests: XCTestCase {

    func testAllDeviceKindsCovered() {
        XCTAssertEqual(Set(ClusterDevice.Kind.allCases),
                       [.watch, .phone, .iPad, .mac])
    }

    func testEachDeviceHasDistinctFunction() {
        let functions = ClusterDevice.Kind.allCases.map(\.function)
        XCTAssertEqual(functions.count, Set(functions).count,
                       "each device should perform a distinct function")
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
}
