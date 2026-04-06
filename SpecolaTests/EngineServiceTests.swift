import XCTest
@testable import Specola

final class EngineServiceTests: XCTestCase {

    // MARK: - parseOutput success cases

    func testParseSuccessOutput() throws {
        let json = """
        {"status": "ok", "output_path": "/path/to/file.docx", "feed_count": 187, "item_count": 42}
        """
        let result = try EngineService.parseOutput(json)
        XCTAssertEqual(result.outputPath, "/path/to/file.docx")
        XCTAssertEqual(result.feedCount, 187)
        XCTAssertEqual(result.itemCount, 42)
    }

    func testParseSuccessWithAllFields() throws {
        let json = """
        {"status": "ok", "output_path": "/path/file.docx", "html_path": "/path/file.html", "feed_count": 50, "item_count": 20, "highlights": ["H1", "H2"]}
        """
        let result = try EngineService.parseOutput(json)
        XCTAssertEqual(result.outputPath, "/path/file.docx")
        XCTAssertEqual(result.htmlPath, "/path/file.html")
        XCTAssertEqual(result.feedCount, 50)
        XCTAssertEqual(result.itemCount, 20)
        XCTAssertEqual(result.highlights, ["H1", "H2"])
    }

    func testParseSuccessMinimalFields() throws {
        let json = """
        {"status": "ok"}
        """
        let result = try EngineService.parseOutput(json)
        XCTAssertNil(result.outputPath)
        XCTAssertNil(result.htmlPath)
        XCTAssertEqual(result.feedCount, 0)
        XCTAssertEqual(result.itemCount, 0)
        XCTAssertEqual(result.highlights, [])
    }

    func testParseSuccessWithNullOptionals() throws {
        let json = """
        {"status": "ok", "output_path": null, "html_path": null, "feed_count": 0, "item_count": 0, "highlights": []}
        """
        let result = try EngineService.parseOutput(json)
        XCTAssertNil(result.outputPath)
        XCTAssertNil(result.htmlPath)
        XCTAssertEqual(result.feedCount, 0)
        XCTAssertEqual(result.itemCount, 0)
    }

    // MARK: - parseOutput error cases

    func testParseErrorOutput() {
        let json = """
        {"status": "error", "message": "Claude CLI non trovata"}
        """
        XCTAssertThrowsError(try EngineService.parseOutput(json)) { error in
            XCTAssertTrue(error.localizedDescription.contains("Claude CLI"))
        }
    }

    func testParseErrorWithoutMessage() {
        let json = """
        {"status": "error"}
        """
        XCTAssertThrowsError(try EngineService.parseOutput(json)) { error in
            XCTAssertTrue(error.localizedDescription.contains("sconosciuto"))
        }
    }

    func testParseInvalidJSON() {
        XCTAssertThrowsError(try EngineService.parseOutput("not json"))
    }

    func testParseEmptyJSON() {
        XCTAssertThrowsError(try EngineService.parseOutput("{}"))
    }

    func testParseEmptyString() {
        XCTAssertThrowsError(try EngineService.parseOutput("")) { error in
            XCTAssertTrue(error.localizedDescription.contains("Invalid"))
        }
    }

    func testParseMissingStatusField() {
        let json = """
        {"output_path": "/path", "feed_count": 10}
        """
        XCTAssertThrowsError(try EngineService.parseOutput(json)) { error in
            XCTAssertTrue(error.localizedDescription.contains("status"))
        }
    }

    func testParseStatusNotString() {
        let json = """
        {"status": 123}
        """
        XCTAssertThrowsError(try EngineService.parseOutput(json)) { error in
            XCTAssertTrue(error.localizedDescription.contains("status"))
        }
    }

    func testParseArrayInsteadOfObject() {
        XCTAssertThrowsError(try EngineService.parseOutput("[1,2,3]")) { error in
            XCTAssertTrue(error.localizedDescription.contains("Invalid JSON"))
        }
    }

    // MARK: - EngineError descriptions

    func testEngineNotFoundDescription() {
        let error = EngineError.engineNotFound
        XCTAssertEqual(error.errorDescription, "Motore Python non trovato")
    }

    func testPythonNotFoundDescription() {
        let error = EngineError.pythonNotFound
        XCTAssertEqual(error.errorDescription, "Python venv non trovato")
    }

    func testExecutionFailedDescription() {
        let error = EngineError.executionFailed("Something went wrong")
        XCTAssertEqual(error.errorDescription, "Something went wrong")
    }

    func testExecutionFailedEmptyMessage() {
        let error = EngineError.executionFailed("")
        XCTAssertEqual(error.errorDescription, "")
    }

    // MARK: - EngineResult struct

    func testEngineResultStoresValues() {
        let result = EngineResult(
            outputPath: "/path/file.docx",
            htmlPath: "/path/file.html",
            feedCount: 100,
            itemCount: 50,
            highlights: ["H1", "H2"]
        )
        XCTAssertEqual(result.outputPath, "/path/file.docx")
        XCTAssertEqual(result.htmlPath, "/path/file.html")
        XCTAssertEqual(result.feedCount, 100)
        XCTAssertEqual(result.itemCount, 50)
        XCTAssertEqual(result.highlights, ["H1", "H2"])
    }

    func testEngineResultOptionalPaths() {
        let result = EngineResult(
            outputPath: nil,
            htmlPath: nil,
            feedCount: 0,
            itemCount: 0,
            highlights: []
        )
        XCTAssertNil(result.outputPath)
        XCTAssertNil(result.htmlPath)
    }

    // MARK: - Unicode handling

    func testParseUnicodeOutput() throws {
        let json = """
        {"status": "ok", "output_path": "/path/Specola_àèìòù.docx", "feed_count": 1, "item_count": 1, "highlights": ["Notizia con accénti"]}
        """
        let result = try EngineService.parseOutput(json)
        XCTAssertTrue(result.outputPath?.contains("àèìòù") ?? false)
        XCTAssertEqual(result.highlights.first, "Notizia con accénti")
    }
}
