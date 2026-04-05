import Foundation
import UserNotifications

enum NotificationService {
    static func requestPermission() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { _, _ in }
    }

    static func notifySuccess(date: String, itemCount: Int, docxPath: String) {
        let content = UNMutableNotificationContent()
        content.title = "Specola del \(date) pronta"
        content.body = "\(itemCount) articoli analizzati"
        content.sound = .default
        content.userInfo = ["docxPath": docxPath]

        let request = UNNotificationRequest(
            identifier: "specola-\(date)",
            content: content,
            trigger: nil
        )
        UNUserNotificationCenter.current().add(request)
    }

    static func notifyError(message: String) {
        let content = UNMutableNotificationContent()
        content.title = "Specola: generazione fallita"
        content.body = message
        content.sound = .default

        let request = UNNotificationRequest(
            identifier: "specola-error-\(Date().timeIntervalSince1970)",
            content: content,
            trigger: nil
        )
        UNUserNotificationCenter.current().add(request)
    }
}
