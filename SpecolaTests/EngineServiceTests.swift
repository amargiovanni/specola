import XCTest
@testable import Specola

final class EngineServiceTests: XCTestCase {
    func testParseSuccessOutput() throws {
        let json = """
        {"status": "ok", "output_path": "/path/to/file.docx", "feed_count": 187, "item_count": 42}
        """
        let result = try EngineService.parseOutput(json)
        XCTAssertEqual(result.outputPath, "/path/to/file.docx")
        XCTAssertEqual(result.feedCount, 187)
        XCTAssertEqual(result.itemCount, 42)
    }

    func testParseErrorOutput() {
        let json = """
        {"status": "error", "message": "Claude CLI non trovata"}
        """
        XCTAssertThrowsError(try EngineService.parseOutput(json)) { error in
            XCTAssertTrue(error.localizedDescription.contains("Claude CLI"))
        }
    }

    func testParseInvalidJSON() {
        XCTAssertThrowsError(try EngineService.parseOutput("not json"))
    }

    func testParseEmptyJSON() {
        XCTAssertThrowsError(try EngineService.parseOutput("{}"))
    }
}
