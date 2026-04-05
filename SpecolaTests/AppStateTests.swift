import XCTest
@testable import Specola

final class AppStateTests: XCTestCase {
    func testUnreadCount() {
        let state = AppState()
        state.history = [
            SpecolaEntry(id: "1", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false),
            SpecolaEntry(id: "2", date: Date(), path: "", feedCount: 0, itemCount: 0, read: true),
            SpecolaEntry(id: "3", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false),
        ]
        XCTAssertEqual(state.unreadCount, 2)
    }

    func testMarkAsRead() {
        let state = AppState()
        let entry = SpecolaEntry(id: "1", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false)
        state.history = [entry]
        state.markAsRead(entry)
        XCTAssertTrue(state.history[0].read)
        XCTAssertEqual(state.unreadCount, 0)
    }

    func testAddEntryEnforcesMax() {
        let state = AppState()
        for i in 0..<35 {
            let entry = SpecolaEntry(id: "\(i)", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false)
            state.addEntry(entry)
        }
        XCTAssertEqual(state.history.count, 30)
    }

    func testHasGeneratedToday() {
        let state = AppState()
        XCTAssertFalse(state.hasGeneratedToday)
        let entry = SpecolaEntry(id: "today", date: Date(), path: "", feedCount: 0, itemCount: 0, read: false)
        state.history = [entry]
        XCTAssertTrue(state.hasGeneratedToday)
    }
}
