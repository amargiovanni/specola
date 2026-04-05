import XCTest
@testable import Specola

final class SchedulerServiceTests: XCTestCase {
    func testShouldNotGenerateBeforeScheduledTime() {
        let result = SchedulerService.shouldGenerate(
            autoGenerate: true, scheduleHour: 7, scheduleMinute: 0,
            hasGeneratedToday: false, now: dateAt(hour: 6, minute: 30))
        XCTAssertFalse(result)
    }

    func testShouldGenerateAtScheduledTime() {
        let result = SchedulerService.shouldGenerate(
            autoGenerate: true, scheduleHour: 7, scheduleMinute: 0,
            hasGeneratedToday: false, now: dateAt(hour: 7, minute: 0))
        XCTAssertTrue(result)
    }

    func testShouldGenerateAfterScheduledTime() {
        let result = SchedulerService.shouldGenerate(
            autoGenerate: true, scheduleHour: 7, scheduleMinute: 0,
            hasGeneratedToday: false, now: dateAt(hour: 10, minute: 30))
        XCTAssertTrue(result)
    }

    func testShouldNotGenerateIfAlreadyDone() {
        let result = SchedulerService.shouldGenerate(
            autoGenerate: true, scheduleHour: 7, scheduleMinute: 0,
            hasGeneratedToday: true, now: dateAt(hour: 10, minute: 0))
        XCTAssertFalse(result)
    }

    func testShouldNotGenerateIfAutoOff() {
        let result = SchedulerService.shouldGenerate(
            autoGenerate: false, scheduleHour: 7, scheduleMinute: 0,
            hasGeneratedToday: false, now: dateAt(hour: 10, minute: 0))
        XCTAssertFalse(result)
    }

    private func dateAt(hour: Int, minute: Int) -> Date {
        var components = Calendar.current.dateComponents([.year, .month, .day], from: Date())
        components.hour = hour
        components.minute = minute
        components.second = 0
        return Calendar.current.date(from: components)!
    }
}
