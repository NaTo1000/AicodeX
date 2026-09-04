import XCTest
@testable import AicodeXApp

final class AicodeXAppTests: XCTestCase {
    func testContentViewBuilds() {
        // The SwiftUI view hierarchy should construct without error.
        let view = ContentView()
        XCTAssertNotNil(view)
    }
}
