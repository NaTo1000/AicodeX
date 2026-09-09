import XCTest
@testable import AicodeXAppTests

fileprivate extension ClusterCoreTests {
    @available(*, deprecated, message: "Not actually deprecated. Marked as deprecated to allow inclusion of deprecated tests (which test deprecated functionality) without warnings")
    static nonisolated(unsafe) let __allTests__ClusterCoreTests = [
        ("testAllDeviceKindsCovered", testAllDeviceKindsCovered),
        ("testAllTabsPresent", testAllTabsPresent),
        ("testApplyingProgressMarksOnlineAndClamps", testApplyingProgressMarksOnlineAndClamps),
        ("testDeviceCodableRoundTrip", testDeviceCodableRoundTrip),
        ("testEachDeviceHasDistinctFunction", testEachDeviceHasDistinctFunction),
        ("testEachDeviceHasDistinctIcon", testEachDeviceHasDistinctIcon),
        ("testEachTabHasDistinctIcon", testEachTabHasDistinctIcon),
        ("testEachTabHasIconAndTitle", testEachTabHasIconAndTitle),
        ("testEveryDeviceIsHD", testEveryDeviceIsHD),
        ("testNon3DDevicesRender2D", testNon3DDevicesRender2D),
        ("testOverallProgress", testOverallProgress),
        ("testProgressClamping", testProgressClamping),
        ("testStorageKey", testStorageKey),
        ("testThreeDCapableDevices", testThreeDCapableDevices)
    ]
}
@available(*, deprecated, message: "Not actually deprecated. Marked as deprecated to allow inclusion of deprecated tests (which test deprecated functionality) without warnings")
func __AicodeXAppTests__allTests() -> [XCTestCaseEntry] {
    return [
        testCase(ClusterCoreTests.__allTests__ClusterCoreTests)
    ]
}