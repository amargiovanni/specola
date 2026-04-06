import WidgetKit

struct SpecolaWidgetEntry: TimelineEntry {
    let date: Date
    let data: WidgetSnapshot
}

struct WidgetSnapshot {
    let briefingDate: Date
    let dateLabel: String
    let unreadCount: Int
    let highlights: [String]
    let latestPath: String
    let isEmpty: Bool

    static let placeholder = WidgetSnapshot(
        briefingDate: .now,
        dateLabel: "6 aprile 2026",
        unreadCount: 2,
        highlights: [
            "EU approva regolamento AI Act",
            "GitHub Copilot Workspace in GA",
            "Vulnerabilita critica OpenSSL 3.x",
        ],
        latestPath: "",
        isEmpty: false
    )

    static let empty = WidgetSnapshot(
        briefingDate: .now,
        dateLabel: "—",
        unreadCount: 0,
        highlights: [],
        latestPath: "",
        isEmpty: true
    )
}

func loadWidgetSnapshot() -> WidgetSnapshot {
    let appGroupID = "group.com.oltrematica.specola"
    guard let container = FileManager.default.containerURL(
        forSecurityApplicationGroupIdentifier: appGroupID
    ) else { return .empty }

    let fileURL = container.appendingPathComponent("widget_data.json")
    guard let data = try? Data(contentsOf: fileURL) else { return .empty }

    let decoder = JSONDecoder()
    decoder.dateDecodingStrategy = .iso8601

    struct RawData: Decodable {
        let date: Date
        let dateLabel: String
        let unreadCount: Int
        let highlights: [String]
        let latestPath: String
    }

    guard let raw = try? decoder.decode(RawData.self, from: data) else { return .empty }

    return WidgetSnapshot(
        briefingDate: raw.date,
        dateLabel: raw.dateLabel,
        unreadCount: raw.unreadCount,
        highlights: raw.highlights,
        latestPath: raw.latestPath,
        isEmpty: false
    )
}
