import SwiftUI
import WidgetKit

struct SpecolaWidgetView: View {
    let entry: SpecolaWidgetEntry
    @Environment(\.widgetFamily) var family

    var body: some View {
        if entry.data.isEmpty {
            emptyState
        } else {
            content
        }
    }

    private var content: some View {
        VStack(alignment: .leading, spacing: 8) {
            header
            Divider()
            sectionTitle
            highlights
            Spacer(minLength: 0)
        }
        .padding()
        .widgetURL(URL(string: "specola://open-latest"))
    }

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("Specola")
                    .font(.headline)
                    .fontWeight(.bold)
                Text(entry.data.dateLabel)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            if entry.data.unreadCount > 0 {
                Text("\(entry.data.unreadCount)")
                    .font(.caption2)
                    .fontWeight(.bold)
                    .foregroundStyle(.white)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color.red, in: Capsule())
            }
        }
    }

    private var sectionTitle: some View {
        Text("Da sapere oggi")
            .font(.subheadline)
            .fontWeight(.semibold)
            .foregroundStyle(Color(red: 0.91, green: 0.27, blue: 0.38))
    }

    private var highlights: some View {
        let maxItems = family == .systemMedium ? 3 : 5
        return VStack(alignment: .leading, spacing: 6) {
            ForEach(
                Array(entry.data.highlights.prefix(maxItems).enumerated()),
                id: \.offset
            ) { _, item in
                HStack(alignment: .top, spacing: 6) {
                    Text("\u{2022}")
                        .foregroundStyle(.secondary)
                    Text(item)
                        .font(.caption)
                        .lineLimit(2)
                }
            }
        }
    }

    private var emptyState: some View {
        VStack(spacing: 8) {
            Text("Specola")
                .font(.headline)
                .fontWeight(.bold)
            Text("Nessun briefing disponibile")
                .font(.caption)
                .foregroundStyle(.secondary)
            Text("Configura l'app per iniziare")
                .font(.caption2)
                .foregroundStyle(.tertiary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding()
    }
}
