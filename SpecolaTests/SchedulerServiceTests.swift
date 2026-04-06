import XCTest
@testable import Specola

final class SchedulerServiceTests: XCTestCase {

    // MARK: - Basic scheduling logic

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

    // MARK: - Minute-level edge cases

    func testShouldNotGenerateOneMinuteBefore() {
        let result = SchedulerService.shouldGenerate(
            autoGenerate: true, scheduleHour: 7, scheduleMinute: 30,
            hasGeneratedToday: false, now: dateAt(hour: 7, minute: 29))
        XCTAssertFalse(result)
    }

    func testShouldGenerateExactMinute() {
        let result = SchedulerService.shouldGenerate(
            autoGenerate: true, scheduleHour: 7, scheduleMinute: 30,
            hasGeneratedToday: false, now: dateAt(hour: 7, minute: 30))
        XCTAssertTrue(result)
    }

    func testShouldGenerateOneMinuteAfter() {
        let result = SchedulerService.shouldGenerate(
            autoGenerate: true, scheduleHour: 7, scheduleMinute: 30,
            hasGeneratedToday: false, now: dateAt(hour: 7, minute: 31))
        XCTAssertTrue(result)
    }

    // MARK: - Hour boundary edge cases

    func testShouldNotGenerateSameHourEarlierMinute() {
        // Schedule at 14:45, current time 14:30
        let result = SchedulerService.shouldGenerate(
            autoGenerate: true, scheduleHour: 14, scheduleMinute: 45,
            hasGeneratedToday: false, now: dateAt(hour: 14, minute: 30))
        XCTAssertFalse(result)
    }

    func testShouldGenerateNextHour() {
        // Schedule at 14:45, current time 15:00
        let result = SchedulerService.shouldGenerate(
            autoGenerate: true, scheduleHour: 14, scheduleMinute: 45,
            hasGeneratedToday: false, now: dateAt(hour: 15, minute: 0))
        XCTAssertTrue(result)
    }

    // MARK: - Midnight edge cases

    func testScheduleAtMidnight() {
        let result = SchedulerService.shouldGenerate(
            autoGenerate: true, scheduleHour: 0, scheduleMinute: 0,
            hasGeneratedToday: false, now: dateAt(hour: 0, minute: 0))
        XCTAssertTrue(result)
    }

    func testScheduleLateNight() {
        let result = SchedulerService.shouldGenerate(
            autoGenerate: true, scheduleHour: 23, scheduleMinute: 59,
            hasGeneratedToday: false, now: dateAt(hour: 23, minute: 59))
        XCTAssertTrue(result)
    }

    func testScheduleAtMidnightBeforeTime() {
        // Schedule at 0:30, current is 0:15
        let result = SchedulerService.shouldGenerate(
            autoGenerate: true, scheduleHour: 0, scheduleMinute: 30,
            hasGeneratedToday: false, now: dateAt(hour: 0, minute: 15))
        XCTAssertFalse(result)
    }

    // MARK: - All conditions combined

    func testAllConditionsMet() {
        let result = SchedulerService.shouldGenerate(
            autoGenerate: true, scheduleHour: 8, scheduleMinute: 0,
            hasGeneratedToday: false, now: dateAt(hour: 9, minute: 0))
        XCTAssertTrue(result)
    }

    func testAutoOffOverridesEverything() {
        let result = SchedulerService.shouldGenerate(
            autoGenerate: false, scheduleHour: 0, scheduleMinute: 0,
            hasGeneratedToday: false, now: dateAt(hour: 23, minute: 59))
        XCTAssertFalse(result)
    }

    func testAlreadyGeneratedOverrides() {
        let result = SchedulerService.shouldGenerate(
            autoGenerate: true, scheduleHour: 0, scheduleMinute: 0,
            hasGeneratedToday: true, now: dateAt(hour: 23, minute: 59))
        XCTAssertFalse(result)
    }

    // MARK: - Default hasGeneratedToday

    func testDefaultHasGeneratedTodayIsFalse() {
        // When hasGeneratedToday is nil, defaults to false
        let result = SchedulerService.shouldGenerate(
            autoGenerate: true, scheduleHour: 7, scheduleMinute: 0,
            hasGeneratedToday: nil, now: dateAt(hour: 10, minute: 0))
        XCTAssertTrue(result)
    }

    // MARK: - Helper

    private func dateAt(hour: Int, minute: Int) -> Date {
        var components = Calendar.current.dateComponents([.year, .month, .day], from: Date())
        components.hour = hour
        components.minute = minute
        components.second = 0
        return Calendar.current.date(from: components)!
    }
}
