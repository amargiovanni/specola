import WidgetKit
import SwiftUI

struct SpecolaProvider: TimelineProvider {
    func placeholder(in context: Context) -> SpecolaWidgetEntry {
        SpecolaWidgetEntry(date: .now, data: .placeholder)
    }

    func getSnapshot(in context: Context, completion: @escaping (SpecolaWidgetEntry) -> Void) {
        let snapshot = loadWidgetSnapshot()
        completion(SpecolaWidgetEntry(date: .now, data: snapshot))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<SpecolaWidgetEntry>) -> Void) {
        let snapshot = loadWidgetSnapshot()
        let entry = SpecolaWidgetEntry(date: .now, data: snapshot)
        let timeline = Timeline(entries: [entry], policy: .never)
        completion(timeline)
    }
}

struct SpecolaWidgetBundle: Widget {
    let kind = "com.oltrematica.specola.widget"

    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: SpecolaProvider()) { entry in
            SpecolaWidgetView(entry: entry)
                .containerBackground(.fill.tertiary, for: .widget)
        }
        .configurationDisplayName("Specola")
        .description("I punti chiave del briefing di oggi")
        .supportedFamilies([.systemMedium, .systemLarge])
    }
}

@main
struct SpecolaWidgets: WidgetBundle {
    var body: some Widget {
        SpecolaWidgetBundle()
    }
}
