import AppKit
import UserNotifications

final class NotificationDelegate: NSObject, UNUserNotificationCenterDelegate {
    static let shared = NotificationDelegate()

    /// Show banner even when app is in foreground (menubar apps are always "foreground")
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        completionHandler([.banner, .sound])
    }

    /// Handle "Apri" action — open the DOCX file
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        if let path = response.notification.request.content.userInfo["docxPath"] as? String {
            NSWorkspace.shared.open(URL(fileURLWithPath: path))
        }
        completionHandler()
    }
}

enum NotificationService {
    static func setup() {
        let center = UNUserNotificationCenter.current()
        center.delegate = NotificationDelegate.shared
        center.requestAuthorization(options: [.alert, .sound, .badge]) { granted, error in
            if let error {
                print("Notification permission error: \(error)")
            }
        }
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
