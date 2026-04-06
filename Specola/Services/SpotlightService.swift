import CoreSpotlight
import UniformTypeIdentifiers

enum SpotlightService {

    /// Index a briefing in Spotlight so it's searchable system-wide.
    static func indexBriefing(_ entry: SpecolaEntry) {
        let attributeSet = CSSearchableItemAttributeSet(contentType: .content)
        attributeSet.title = "Specola — \(formattedDate(entry.date))"
        attributeSet.contentDescription = entry.highlights.prefix(3).joined(separator: ". ")
        attributeSet.keywords = ["specola", "briefing", "rss", "news"]
            + entry.highlights.prefix(5)

        // Add metadata
        attributeSet.contentCreationDate = entry.date
        attributeSet.metadataModificationDate = entry.date

        // Link to the HTML file if available, otherwise the main file
        let filePath = entry.htmlPath.isEmpty ? entry.path : entry.htmlPath
        if !filePath.isEmpty {
            attributeSet.contentURL = URL(fileURLWithPath: filePath)
        }

        let item = CSSearchableItem(
            uniqueIdentifier: "specola-\(entry.id)",
            domainIdentifier: "com.oltrematica.specola.briefings",
            attributeSet: attributeSet
        )
        item.expirationDate = Calendar.current.date(byAdding: .month, value: 6, to: entry.date)

        CSSearchableIndex.default().indexSearchableItems([item])
    }

    /// Remove a briefing from Spotlight index.
    static func removeBriefing(id: String) {
        CSSearchableIndex.default().deleteSearchableItems(
            withIdentifiers: ["specola-\(id)"]
        )
    }

    /// Re-index all briefings (e.g., on app launch).
    static func reindexAll(history: [SpecolaEntry]) {
        // Remove stale items
        CSSearchableIndex.default().deleteSearchableItems(
            withDomainIdentifiers: ["com.oltrematica.specola.briefings"]
        ) { _ in
            // Re-index current history
            let items = history.map { entry -> CSSearchableItem in
                let attrs = CSSearchableItemAttributeSet(contentType: .content)
                attrs.title = "Specola — \(formattedDate(entry.date))"
                attrs.contentDescription = entry.highlights.prefix(3).joined(separator: ". ")
                attrs.keywords = ["specola", "briefing", "rss"]
                attrs.contentCreationDate = entry.date
                let filePath = entry.htmlPath.isEmpty ? entry.path : entry.htmlPath
                if !filePath.isEmpty {
                    attrs.contentURL = URL(fileURLWithPath: filePath)
                }
                let item = CSSearchableItem(
                    uniqueIdentifier: "specola-\(entry.id)",
                    domainIdentifier: "com.oltrematica.specola.briefings",
                    attributeSet: attrs
                )
                item.expirationDate = Calendar.current.date(byAdding: .month, value: 6, to: entry.date)
                return item
            }
            if !items.isEmpty {
                CSSearchableIndex.default().indexSearchableItems(items)
            }
        }
    }

    private static func formattedDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .long
        formatter.locale = Locale(identifier: SpecolaSettings.language == "it" ? "it_IT" : "en_US")
        return formatter.string(from: date)
    }
}
