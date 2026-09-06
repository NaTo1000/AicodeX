import XCTest
@testable import AicodeXCoreTests

fileprivate extension AicodeXCoreTests {
    @available(*, deprecated, message: "Not actually deprecated. Marked as deprecated to allow inclusion of deprecated tests (which test deprecated functionality) without warnings")
    static nonisolated(unsafe) let __allTests__AicodeXCoreTests = [
        ("testDefaultSettingsMatchPythonConfig", testDefaultSettingsMatchPythonConfig),
        ("testDownloadChecksumMismatchThrows", asyncTest(testDownloadChecksumMismatchThrows)),
        ("testHotkeyLookup", testHotkeyLookup),
        ("testInfoDictionary", testInfoDictionary),
        ("testOpacityClamping", testOpacityClamping),
        ("testQuickActionDefaultsMirrorPython", testQuickActionDefaultsMirrorPython),
        ("testSHA256ABC", testSHA256ABC),
        ("testSHA256Empty", testSHA256Empty),
        ("testSHA256MultiBlock", testSHA256MultiBlock),
        ("testSettingsRoundTrip", testSettingsRoundTrip),
        ("testSnippetAddRemove", testSnippetAddRemove),
        ("testSnippetLanguages", testSnippetLanguages),
        ("testSnippetSearchFilters", testSnippetSearchFilters),
        ("testVerifyMatchingData", asyncTest(testVerifyMatchingData)),
        ("testVersionSummaryParity", testVersionSummaryParity)
    ]
}
@available(*, deprecated, message: "Not actually deprecated. Marked as deprecated to allow inclusion of deprecated tests (which test deprecated functionality) without warnings")
func __AicodeXCoreTests__allTests() -> [XCTestCaseEntry] {
    return [
        testCase(AicodeXCoreTests.__allTests__AicodeXCoreTests)
    ]
}