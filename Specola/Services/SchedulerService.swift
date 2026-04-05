import Foundation
import AppKit

final class SchedulerService {
    private var timer: Timer?
    private var onTrigger: (() -> Void)?

    func start(onTrigger: @escaping () -> Void) {
        self.onTrigger = onTrigger
        timer = Timer.scheduledTimer(withTimeInterval: 60, repeats: true) { [weak self] _ in
            self?.checkAndTrigger()
        }
        NSWorkspace.shared.notificationCenter.addObserver(
            self,
            selector: #selector(handleWake),
            name: NSWorkspace.didWakeNotification,
            object: nil
        )
    }

    func stop() {
        timer?.invalidate()
        timer = nil
        NSWorkspace.shared.notificationCenter.removeObserver(self)
    }

    @objc private func handleWake() {
        DispatchQueue.main.asyncAfter(deadline: .now() + 5) { [weak self] in
            self?.checkAndTrigger()
        }
    }

    private func checkAndTrigger() {
        if Self.shouldGenerate() {
            onTrigger?()
        }
    }

    static func shouldGenerate(
        autoGenerate: Bool? = nil,
        scheduleHour: Int? = nil,
        scheduleMinute: Int? = nil,
        hasGeneratedToday: Bool? = nil,
        now: Date = Date()
    ) -> Bool {
        let auto = autoGenerate ?? SpecolaSettings.autoGenerate
        guard auto else { return false }

        let hour = scheduleHour ?? SpecolaSettings.scheduleHour
        let minute = scheduleMinute ?? SpecolaSettings.scheduleMinute

        let calendar = Calendar.current
        let components = calendar.dateComponents([.hour, .minute], from: now)
        let currentHour = components.hour ?? 0
        let currentMinute = components.minute ?? 0

        let isPastSchedule = currentHour > hour || (currentHour == hour && currentMinute >= minute)
        guard isPastSchedule else { return false }

        let generated = hasGeneratedToday ?? false
        return !generated
    }
}
