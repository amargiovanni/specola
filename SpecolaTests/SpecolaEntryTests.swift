import XCTest
@testable import Specola

final class SpecolaEntryTests: XCTestCase {
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
}
