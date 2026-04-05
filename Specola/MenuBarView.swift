import SwiftUI

struct MenuBarView: View {
    @Environment(AppState.self) private var appState
    @Environment(\.openSettings) private var openSettings

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header
            VStack(alignment: .leading, spacing: 2) {
                Text("Specola")
                    .font(.headline)
                    .fontWeight(.bold)

                if let lastDate = appState.lastGeneration {
                    Text("Ultima generazione: \(lastDate.formatted(date: .long, time: .shortened))")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                } else {
                    Text("Nessuna Specola generata")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(.horizontal, 16)
            .padding(.top, 12)
            .padding(.bottom, 8)

            Divider()

            // List
            if appState.history.isEmpty {
                Text("Nessuna Specola disponibile")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical, 24)
            } else {
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 0) {
                        ForEach(appState.history.prefix(10)) { entry in
                            SpecolaRow(entry: entry)
                                .onTapGesture { openSpecola(entry) }
                        }
                    }
                }
                .frame(maxHeight: 300)
            }

            Divider()

            // Actions
            VStack(spacing: 8) {
                if appState.isGenerating {
                    HStack {
                        ProgressView()
                            .controlSize(.small)
                        Text("Generazione in corso...")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.vertical, 4)
                } else {
                    Button("Genera ora") {
                        generateNow()
                    }
                    .disabled(!appState.canGenerate)
                    .frame(maxWidth: .infinity)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 8)

            Divider()

            // Footer
            HStack {
                Button("Impostazioni...") {
                    openSettings()
                }

                Spacer()

                Button("Esci") {
                    NSApplication.shared.terminate(nil)
                }
                .buttonStyle(.plain)
                .foregroundStyle(.secondary)
            }
            .font(.subheadline)
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
        }
        .frame(width: 320)
    }

    private func openSpecola(_ entry: SpecolaEntry) {
        let url = URL(fileURLWithPath: entry.path)
        NSWorkspace.shared.open(url)
        appState.markAsRead(entry)
    }

    private func generateNow() {
        appState.isGenerating = true
        appState.lastError = nil

        Task {
            do {
                let result = try await EngineService.run()
                let entry = SpecolaEntry(
                    id: dateId(),
                    date: Date(),
                    path: result.outputPath ?? "",
                    feedCount: result.feedCount,
                    itemCount: result.itemCount,
                    read: false
                )
                await MainActor.run {
                    appState.addEntry(entry)
                    appState.isGenerating = false
                }
                if let path = result.outputPath {
                    NotificationService.notifySuccess(
                        date: dateId(),
                        itemCount: result.itemCount,
                        docxPath: path
                    )
                }
            } catch {
                await MainActor.run {
                    appState.isGenerating = false
                    appState.lastError = error.localizedDescription
                }
                NotificationService.notifyError(message: error.localizedDescription)
            }
        }
    }

    private func dateId() -> String {
        let fmt = DateFormatter()
        fmt.dateFormat = "yyyy-MM-dd"
        return fmt.string(from: Date())
    }
}

private struct SpecolaRow: View {
    let entry: SpecolaEntry

    var body: some View {
        HStack(spacing: 10) {
            Circle()
                .fill(entry.read ? Color.clear : Color.accentColor)
                .frame(width: 8, height: 8)

            VStack(alignment: .leading, spacing: 2) {
                Text(entry.date.formatted(date: .long, time: .omitted))
                    .font(.subheadline)
                    .fontWeight(entry.read ? .regular : .semibold)

                Text("\(entry.feedCount) fonti · \(entry.itemCount) articoli")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer()
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 6)
        .contentShape(Rectangle())
        .background(Color.primary.opacity(0.001))
    }
}
