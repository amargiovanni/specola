import Foundation
import Observation
import WidgetKit

@Observable
final class AppState {
    var history: [SpecolaEntry] = []
    var isGenerating: Bool = false
    var lastError: String?

    private static let maxHistoryEntries = 30

    var unreadCount: Int {
        history.filter { !$0.read }.count
    }

    var lastGeneration: Date? {
        history.first?.date
    }

    var hasGeneratedToday: Bool {
        guard let last = history.first else { return false }
        return Calendar.current.isDateInToday(last.date)
    }

    var canGenerate: Bool {
        !isGenerating && SpecolaSettings.hasOPML
    }

    /// Item counts from last 7 entries (oldest first) for the menubar sparkline.
    var sparklineData: [Int] {
        Array(history.prefix(7).map(\.itemCount).reversed())
    }

    func loadHistory() {
        let path = SpecolaSettings.historyPath
        guard FileManager.default.fileExists(atPath: path.path) else { return }
        do {
            let data = try Data(contentsOf: path)
            let decoder = JSONDecoder()
            decoder.dateDecodingStrategy = .iso8601
            history = try decoder.decode([SpecolaEntry].self, from: data)
            SpotlightService.reindexAll(history: history)
        } catch {
            history = []
        }
    }

    func saveHistory() {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        do {
            let data = try encoder.encode(history)
            try data.write(to: SpecolaSettings.historyPath)
        } catch { }
    }

    func addEntry(_ entry: SpecolaEntry) {
        history.insert(entry, at: 0)
        if history.count > Self.maxHistoryEntries {
            history = Array(history.prefix(Self.maxHistoryEntries))
        }
        saveHistory()
        updateWidgetData()
        SpotlightService.indexBriefing(entry)
    }

    func markAsRead(_ entry: SpecolaEntry) {
        guard let index = history.firstIndex(where: { $0.id == entry.id }) else { return }
        history[index].read = true
        saveHistory()
        updateWidgetData()
    }

    func updateWidgetData() {
        guard let latest = history.first,
              let url = WidgetData.fileURL else { return }

        let formatter = DateFormatter()
        formatter.dateStyle = .long
        formatter.locale = Locale(identifier: SpecolaSettings.language == "it" ? "it_IT" : "en_US")
        let dateLabel = formatter.string(from: latest.date)

        let data = WidgetData(
            date: latest.date,
            dateLabel: dateLabel,
            unreadCount: unreadCount,
            highlights: latest.highlights,
            latestPath: latest.path
        )
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        try? encoder.encode(data).write(to: url)
        WidgetCenter.shared.reloadAllTimelines()
    }

    func loadProfile() -> String {
        let path = SpecolaSettings.profilePath
        return (try? String(contentsOf: path, encoding: .utf8)) ?? ""
    }

    func saveProfile(_ text: String) {
        try? text.write(to: SpecolaSettings.profilePath, atomically: true, encoding: .utf8)
    }
}
