import XCTest
@testable import Specola

final class SpecolaEntryTests: XCTestCase {

    // MARK: - Encoding / Decoding

    func testEncodeDecode() throws {
        let entry = SpecolaEntry(
            id: "2026-04-05",
            date: ISO8601DateFormatter().date(from: "2026-04-05T07:00:00Z")!,
            path: "/Users/test/Documents/Specola/Specola_2026-04-05.docx",
            feedCount: 187,
            itemCount: 42,
            read: false
        )
        let data = try JSONEncoder().encode(entry)
        let decoded = try JSONDecoder().decode(SpecolaEntry.self, from: data)
        XCTAssertEqual(entry.id, decoded.id)
        XCTAssertEqual(entry.feedCount, decoded.feedCount)
        XCTAssertEqual(entry.itemCount, decoded.itemCount)
        XCTAssertEqual(entry.read, decoded.read)
        XCTAssertEqual(entry.path, decoded.path)
    }

    func testDecodesFromHistoryJSON() throws {
        let json = """
        {"id": "2026-04-05", "date": "2026-04-05T07:00:00Z", "path": "/Users/test/Specola_2026-04-05.docx", "feedCount": 187, "itemCount": 42, "read": false}
        """.data(using: .utf8)!
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let entry = try decoder.decode(SpecolaEntry.self, from: json)
        XCTAssertEqual(entry.id, "2026-04-05")
        XCTAssertEqual(entry.feedCount, 187)
        XCTAssertFalse(entry.read)
    }

    // MARK: - Backward compatibility (missing optional fields)

    func testDecodesWithoutHtmlPath() throws {
        let json = """
        {"id": "2026-04-05", "date": "2026-04-05T07:00:00Z", "path": "/path/file.docx", "feedCount": 10, "itemCount": 5, "read": true}
        """.data(using: .utf8)!
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let entry = try decoder.decode(SpecolaEntry.self, from: json)
        XCTAssertEqual(entry.htmlPath, "")
    }

    func testDecodesWithoutHighlights() throws {
        let json = """
        {"id": "2026-04-05", "date": "2026-04-05T07:00:00Z", "path": "/path/file.docx", "feedCount": 10, "itemCount": 5, "read": false}
        """.data(using: .utf8)!
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let entry = try decoder.decode(SpecolaEntry.self, from: json)
        XCTAssertEqual(entry.highlights, [])
    }

    func testDecodesWithHtmlPathAndHighlights() throws {
        let json = """
        {"id": "2026-04-05", "date": "2026-04-05T07:00:00Z", "path": "/path/file.docx", "htmlPath": "/path/file.html", "feedCount": 10, "itemCount": 5, "highlights": ["Item 1", "Item 2"], "read": false}
        """.data(using: .utf8)!
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let entry = try decoder.decode(SpecolaEntry.self, from: json)
        XCTAssertEqual(entry.htmlPath, "/path/file.html")
        XCTAssertEqual(entry.highlights, ["Item 1", "Item 2"])
    }

    // MARK: - Equatable

    func testEqualEntries() {
        let date = Date()
        let a = SpecolaEntry(id: "1", date: date, path: "/a", feedCount: 10, itemCount: 5, read: false)
        let b = SpecolaEntry(id: "1", date: date, path: "/a", feedCount: 10, itemCount: 5, read: false)
        XCTAssertEqual(a, b)
    }

    func testNotEqualDifferentId() {
        let date = Date()
        let a = SpecolaEntry(id: "1", date: date, path: "/a", feedCount: 10, itemCount: 5, read: false)
        let b = SpecolaEntry(id: "2", date: date, path: "/a", feedCount: 10, itemCount: 5, read: false)
        XCTAssertNotEqual(a, b)
    }

    func testNotEqualDifferentRead() {
        let date = Date()
        let a = SpecolaEntry(id: "1", date: date, path: "/a", feedCount: 10, itemCount: 5, read: false)
        var b = SpecolaEntry(id: "1", date: date, path: "/a", feedCount: 10, itemCount: 5, read: true)
        XCTAssertNotEqual(a, b)
    }

    // MARK: - Identifiable

    func testIdentifiable() {
        let entry = SpecolaEntry(id: "my-id", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false)
        XCTAssertEqual(entry.id, "my-id")
    }

    // MARK: - Default parameter values

    func testDefaultHtmlPathIsEmpty() {
        let entry = SpecolaEntry(id: "1", date: Date(), path: "/a", feedCount: 0, itemCount: 0, read: false)
        XCTAssertEqual(entry.htmlPath, "")
    }

    func testDefaultHighlightsIsEmpty() {
        let entry = SpecolaEntry(id: "1", date: Date(), path: "/a", feedCount: 0, itemCount: 0, read: false)
        XCTAssertEqual(entry.highlights, [])
    }

    // MARK: - Mutability

    func testReadIsMutable() {
        var entry = SpecolaEntry(id: "1", date: Date(), path: "/a", feedCount: 0, itemCount: 0, read: false)
        XCTAssertFalse(entry.read)
        entry.read = true
        XCTAssertTrue(entry.read)
    }

    // MARK: - Round-trip with ISO8601

    func testISO8601RoundTrip() throws {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        let original = SpecolaEntry(
            id: "test", date: Date(timeIntervalSince1970: 1774000000),
            path: "/p", htmlPath: "/h", feedCount: 100, itemCount: 50,
            highlights: ["H1", "H2", "H3"], read: true
        )
        let data = try encoder.encode(original)
        let decoded = try decoder.decode(SpecolaEntry.self, from: data)
        XCTAssertEqual(original.id, decoded.id)
        XCTAssertEqual(original.path, decoded.path)
        XCTAssertEqual(original.htmlPath, decoded.htmlPath)
        XCTAssertEqual(original.feedCount, decoded.feedCount)
        XCTAssertEqual(original.itemCount, decoded.itemCount)
        XCTAssertEqual(original.highlights, decoded.highlights)
        XCTAssertEqual(original.read, decoded.read)
    }
}
