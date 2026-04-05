import Foundation
import Observation

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

    func loadHistory() {
        let path = SpecolaSettings.historyPath
        guard FileManager.default.fileExists(atPath: path.path) else { return }
        do {
            let data = try Data(contentsOf: path)
            let decoder = JSONDecoder()
            decoder.dateDecodingStrategy = .iso8601
            history = try decoder.decode([SpecolaEntry].self, from: data)
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
    }

    func markAsRead(_ entry: SpecolaEntry) {
        guard let index = history.firstIndex(where: { $0.id == entry.id }) else { return }
        history[index].read = true
        saveHistory()
    }

    func loadProfile() -> String {
        let path = SpecolaSettings.profilePath
        return (try? String(contentsOf: path, encoding: .utf8)) ?? ""
    }

    func saveProfile(_ text: String) {
        try? text.write(to: SpecolaSettings.profilePath, atomically: true, encoding: .utf8)
    }
}
