import XCTest
@testable import Specola

final class WidgetDataTests: XCTestCase {

    // MARK: - Encoding / Decoding

    func testEncodeDecode() throws {
        let original = WidgetData(
            date: Date(timeIntervalSince1970: 1774000000),
            dateLabel: "5 aprile 2026",
            unreadCount: 3,
            highlights: ["Item 1", "Item 2"],
            latestPath: "/path/to/file.docx"
        )
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let data = try encoder.encode(original)

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let decoded = try decoder.decode(WidgetData.self, from: data)

        XCTAssertEqual(decoded.dateLabel, "5 aprile 2026")
        XCTAssertEqual(decoded.unreadCount, 3)
        XCTAssertEqual(decoded.highlights, ["Item 1", "Item 2"])
        XCTAssertEqual(decoded.latestPath, "/path/to/file.docx")
    }

    func testEncodeDecodeEmptyHighlights() throws {
        let original = WidgetData(
            date: Date(),
            dateLabel: "Today",
            unreadCount: 0,
            highlights: [],
            latestPath: ""
        )
        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(WidgetData.self, from: data)
        XCTAssertEqual(decoded.highlights, [])
        XCTAssertEqual(decoded.latestPath, "")
    }

    // MARK: - Placeholder

    func testPlaceholderValues() {
        let placeholder = WidgetData.placeholder
        XCTAssertEqual(placeholder.dateLabel, "—")
        XCTAssertEqual(placeholder.unreadCount, 0)
        XCTAssertEqual(placeholder.highlights, [])
        XCTAssertEqual(placeholder.latestPath, "")
    }

    // MARK: - App Group ID

    func testAppGroupID() {
        XCTAssertEqual(WidgetData.appGroupID, "group.com.oltrematica.specola")
        XCTAssertFalse(WidgetData.appGroupID.isEmpty)
    }

    // MARK: - Unicode support

    func testUnicodeHighlights() throws {
        let original = WidgetData(
            date: Date(),
            dateLabel: "5 aprile 2026",
            unreadCount: 1,
            highlights: ["Notizia con àèìòù", "日本語テスト"],
            latestPath: "/path/file.docx"
        )
        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(WidgetData.self, from: data)
        XCTAssertEqual(decoded.highlights[0], "Notizia con àèìòù")
        XCTAssertEqual(decoded.highlights[1], "日本語テスト")
    }

    // MARK: - Five highlights (widget limit)

    func testFiveHighlights() throws {
        let highlights = (1...5).map { "Highlight \($0)" }
        let original = WidgetData(
            date: Date(),
            dateLabel: "Today",
            unreadCount: 1,
            highlights: highlights,
            latestPath: "/p"
        )
        let data = try JSONEncoder().encode(original)
        let decoded = try JSONDecoder().decode(WidgetData.self, from: data)
        XCTAssertEqual(decoded.highlights.count, 5)
    }
}
