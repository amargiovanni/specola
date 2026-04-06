import Foundation

struct WidgetData: Codable {
    let date: Date
    let dateLabel: String
    let unreadCount: Int
    let highlights: [String]
    let latestPath: String

    static let placeholder = WidgetData(
        date: .now,
        dateLabel: "—",
        unreadCount: 0,
        highlights: [],
        latestPath: ""
    )

    static let appGroupID = "group.com.oltrematica.specola"

    static var sharedContainerURL: URL? {
        FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroupID)
    }

    static var fileURL: URL? {
        sharedContainerURL?.appendingPathComponent("widget_data.json")
    }
}
