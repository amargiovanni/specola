import XCTest
@testable import Specola

final class AppStateTests: XCTestCase {

    // MARK: - Unread Count

    func testUnreadCount() {
        let state = AppState()
        state.history = [
            SpecolaEntry(id: "1", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false),
            SpecolaEntry(id: "2", date: Date(), path: "", feedCount: 0, itemCount: 0, read: true),
            SpecolaEntry(id: "3", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false),
        ]
        XCTAssertEqual(state.unreadCount, 2)
    }

    func testUnreadCountAllRead() {
        let state = AppState()
        state.history = [
            SpecolaEntry(id: "1", date: Date(), path: "", feedCount: 0, itemCount: 0, read: true),
            SpecolaEntry(id: "2", date: Date(), path: "", feedCount: 0, itemCount: 0, read: true),
        ]
        XCTAssertEqual(state.unreadCount, 0)
    }

    func testUnreadCountAllUnread() {
        let state = AppState()
        state.history = [
            SpecolaEntry(id: "1", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false),
            SpecolaEntry(id: "2", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false),
        ]
        XCTAssertEqual(state.unreadCount, 2)
    }

    func testUnreadCountEmpty() {
        let state = AppState()
        XCTAssertEqual(state.unreadCount, 0)
    }

    // MARK: - Mark As Read

    func testMarkAsRead() {
        let state = AppState()
        let entry = SpecolaEntry(id: "1", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false)
        state.history = [entry]
        state.markAsRead(entry)
        XCTAssertTrue(state.history[0].read)
        XCTAssertEqual(state.unreadCount, 0)
    }

    func testMarkAsReadNonExistentEntry() {
        let state = AppState()
        let entry1 = SpecolaEntry(id: "1", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false)
        let entry2 = SpecolaEntry(id: "2", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false)
        state.history = [entry1]
        state.markAsRead(entry2)  // Should not crash
        XCTAssertFalse(state.history[0].read)  // entry1 still unread
    }

    func testMarkAsReadAlreadyRead() {
        let state = AppState()
        let entry = SpecolaEntry(id: "1", date: Date(), path: "", feedCount: 0, itemCount: 0, read: true)
        state.history = [entry]
        state.markAsRead(entry)  // Should not crash
        XCTAssertTrue(state.history[0].read)
    }

    // MARK: - Add Entry

    func testAddEntryEnforcesMax() {
        let state = AppState()
        for i in 0..<35 {
            let entry = SpecolaEntry(id: "\(i)", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false)
            state.addEntry(entry)
        }
        XCTAssertEqual(state.history.count, 30)
    }

    func testAddEntryInsertsAtFront() {
        let state = AppState()
        let first = SpecolaEntry(id: "first", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false)
        let second = SpecolaEntry(id: "second", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false)
        state.addEntry(first)
        state.addEntry(second)
        XCTAssertEqual(state.history[0].id, "second")
        XCTAssertEqual(state.history[1].id, "first")
    }

    func testAddEntryExactly30() {
        let state = AppState()
        for i in 0..<30 {
            let entry = SpecolaEntry(id: "\(i)", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false)
            state.addEntry(entry)
        }
        XCTAssertEqual(state.history.count, 30)
    }

    func testAddEntry31DropOldest() {
        let state = AppState()
        for i in 0..<31 {
            let entry = SpecolaEntry(id: "\(i)", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false)
            state.addEntry(entry)
        }
        XCTAssertEqual(state.history.count, 30)
        XCTAssertEqual(state.history.last?.id, "1")  // "0" was dropped
    }

    // MARK: - Has Generated Today

    func testHasGeneratedToday() {
        let state = AppState()
        XCTAssertFalse(state.hasGeneratedToday)
        let entry = SpecolaEntry(id: "today", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false)
        state.history = [entry]
        XCTAssertTrue(state.hasGeneratedToday)
    }

    func testHasNotGeneratedTodayYesterday() {
        let state = AppState()
        let yesterday = Calendar.current.date(byAdding: .day, value: -1, to: Date())!
        let entry = SpecolaEntry(id: "yesterday", date: yesterday, path: "", feedCount: 0, itemCount: 0, read: false)
        state.history = [entry]
        XCTAssertFalse(state.hasGeneratedToday)
    }

    func testHasGeneratedTodayEmptyHistory() {
        let state = AppState()
        XCTAssertFalse(state.hasGeneratedToday)
    }

    // MARK: - Last Generation

    func testLastGenerationReturnsFirstEntry() {
        let state = AppState()
        let date1 = Date(timeIntervalSince1970: 1000)
        let date2 = Date(timeIntervalSince1970: 2000)
        state.history = [
            SpecolaEntry(id: "1", date: date2, path: "", feedCount: 0, itemCount: 0, read: false),
            SpecolaEntry(id: "2", date: date1, path: "", feedCount: 0, itemCount: 0, read: false),
        ]
        XCTAssertEqual(state.lastGeneration, date2)
    }

    func testLastGenerationNilWhenEmpty() {
        let state = AppState()
        XCTAssertNil(state.lastGeneration)
    }

    // MARK: - Is Generating

    func testIsGeneratingDefault() {
        let state = AppState()
        XCTAssertFalse(state.isGenerating)
    }

    func testIsGeneratingToggle() {
        let state = AppState()
        state.isGenerating = true
        XCTAssertTrue(state.isGenerating)
        state.isGenerating = false
        XCTAssertFalse(state.isGenerating)
    }

    // MARK: - Last Error

    func testLastErrorDefault() {
        let state = AppState()
        XCTAssertNil(state.lastError)
    }

    func testLastErrorSetAndClear() {
        let state = AppState()
        state.lastError = "Something failed"
        XCTAssertEqual(state.lastError, "Something failed")
        state.lastError = nil
        XCTAssertNil(state.lastError)
    }
}
