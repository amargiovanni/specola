import SwiftUI
import ServiceManagement
import UniformTypeIdentifiers

struct SettingsView: View {
    var body: some View {
        TabView {
            SourcesTab()
                .tabItem { Label("Fonti", systemImage: "doc.text") }
            ScheduleTab()
                .tabItem { Label("Pianificazione", systemImage: "clock") }
            ProfileTab()
                .tabItem { Label("Profilo", systemImage: "person") }
            AdvancedTab()
                .tabItem { Label("Avanzate", systemImage: "gearshape.2") }
        }
        .frame(width: 520, height: 420)
    }
}

private struct SourcesTab: View {
    @State private var opmlInfo: String = ""
    @State private var opmlConfigured: Bool = SpecolaSettings.hasOPML

    var body: some View {
        Form {
            Section {
                if opmlConfigured {
                    LabeledContent("File OPML") {
                        Text(SpecolaSettings.opmlPath.lastPathComponent)
                            .foregroundStyle(.secondary)
                    }
                    if !opmlInfo.isEmpty {
                        Text(opmlInfo)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                } else {
                    Text("Nessun file OPML configurato")
                        .foregroundStyle(.secondary)
                }
                HStack {
                    Button("Scegli file OPML...") { chooseOPML() }
                    if opmlConfigured {
                        Button("Rimuovi", role: .destructive) { removeOPML() }
                    }
                }
            }
        }
        .formStyle(.grouped)
        .onAppear { refreshOPMLInfo() }
    }

    private func chooseOPML() {
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [
            UTType(filenameExtension: "opml") ?? .xml,
            .xml,
        ]
        panel.allowsMultipleSelection = false
        panel.canChooseDirectories = false
        guard panel.runModal() == .OK, let url = panel.url else { return }
        let dest = SpecolaSettings.opmlPath
        try? FileManager.default.removeItem(at: dest)
        try? FileManager.default.copyItem(at: url, to: dest)
        opmlConfigured = true
        refreshOPMLInfo()
    }

    private func removeOPML() {
        try? FileManager.default.removeItem(at: SpecolaSettings.opmlPath)
        opmlConfigured = false
        opmlInfo = ""
    }

    private func refreshOPMLInfo() {
        guard SpecolaSettings.hasOPML else { opmlInfo = ""; return }
        do {
            let data = try Data(contentsOf: SpecolaSettings.opmlPath)
            let xml = try XMLDocument(data: data)
            let categories = try xml.nodes(forXPath: "/opml/body/outline")
            let feeds = try xml.nodes(forXPath: "//outline[@type='rss']")
            opmlInfo = "\(categories.count) categorie, \(feeds.count) feed"
        } catch {
            opmlInfo = "Errore nella lettura del file OPML"
        }
    }
}

private struct ScheduleTab: View {
    @State private var scheduleDate = scheduleDateFromSettings()
    @State private var autoGenerate = SpecolaSettings.autoGenerate
    @State private var launchAtLogin = SpecolaSettings.launchAtLogin

    var body: some View {
        Form {
            Section {
                DatePicker("Orario generazione", selection: $scheduleDate, displayedComponents: .hourAndMinute)
                    .onChange(of: scheduleDate) { _, newValue in
                        let comps = Calendar.current.dateComponents([.hour, .minute], from: newValue)
                        SpecolaSettings.scheduleHour = comps.hour ?? 7
                        SpecolaSettings.scheduleMinute = comps.minute ?? 0
                    }
                Toggle("Genera automaticamente", isOn: $autoGenerate)
                    .onChange(of: autoGenerate) { _, val in SpecolaSettings.autoGenerate = val }
                Text("Se il Mac è in stop all'orario previsto, la Specola verrà generata al risveglio.")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Section {
                Toggle("Avvia Specola al login", isOn: $launchAtLogin)
                    .onChange(of: launchAtLogin) { _, val in
                        SpecolaSettings.launchAtLogin = val
                        if val {
                            try? SMAppService.mainApp.register()
                        } else {
                            try? SMAppService.mainApp.unregister()
                        }
                    }
            }
        }
        .formStyle(.grouped)
    }

    private static func scheduleDateFromSettings() -> Date {
        var comps = Calendar.current.dateComponents([.year, .month, .day], from: Date())
        comps.hour = SpecolaSettings.scheduleHour
        comps.minute = SpecolaSettings.scheduleMinute
        return Calendar.current.date(from: comps) ?? Date()
    }
}

private struct ProfileTab: View {
    @State private var profileText: String = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Descrivi il tuo ruolo professionale, il tuo stack, i tuoi interessi e progetti. Specola usa questo profilo per personalizzare l'analisi delle notizie.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .padding(.horizontal, 16)
                .padding(.top, 12)

            TextEditor(text: $profileText)
                .font(.body)
                .frame(minHeight: 200)
                .padding(4)
                .overlay(
                    Group {
                        if profileText.isEmpty {
                            Text("Es: Sono CTO di una startup fintech a Milano. Stack: Node.js, TypeScript, AWS. Mi interessa: regolamentazione EU, sicurezza API, trend VC europeo...")
                                .foregroundStyle(.tertiary)
                                .padding(8)
                                .allowsHitTesting(false)
                        }
                    },
                    alignment: .topLeading
                )
                .padding(.horizontal, 16)

            Spacer()
        }
        .onAppear {
            profileText = (try? String(contentsOf: SpecolaSettings.profilePath, encoding: .utf8)) ?? ""
        }
        .onDisappear {
            saveProfile()
        }
    }

    private func saveProfile() {
        guard !profileText.isEmpty else { return }
        try? profileText.write(to: SpecolaSettings.profilePath, atomically: true, encoding: .utf8)
    }
}

private struct AdvancedTab: View {
    @State private var outputDir = SpecolaSettings.outputDir
    @State private var language = SpecolaSettings.language
    @State private var hours = SpecolaSettings.hours
    @State private var claudePath = SpecolaSettings.claudePath
    @State private var outputFormat = SpecolaSettings.outputFormat
    @State private var llmProvider = SpecolaSettings.llmProvider
    @State private var openaiApiKey = SpecolaSettings.openaiApiKey
    @State private var openaiModel = SpecolaSettings.openaiModel
    @State private var lmstudioEndpoint = SpecolaSettings.lmstudioEndpoint
    @State private var lmstudioModel = SpecolaSettings.lmstudioModel

    var body: some View {
        Form {
            Section("Output") {
                LabeledContent("Directory output") {
                    HStack {
                        Text(outputDir)
                            .lineLimit(1)
                            .truncationMode(.middle)
                            .foregroundStyle(.secondary)
                        Button("Apri cartella") {
                            let url = URL(fileURLWithPath: outputDir)
                            try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
                            NSWorkspace.shared.open(url)
                        }
                    }
                }
            }
            Section("Briefing") {
                Picker("Formato di output", selection: $outputFormat) {
                    Text("DOCX").tag("docx")
                    Text("PDF").tag("pdf")
                    Text("EPUB").tag("epub")
                }
                .pickerStyle(.segmented)
                .onChange(of: outputFormat) { _, val in SpecolaSettings.outputFormat = val }

                Picker("Lingua", selection: $language) {
                    Text("Italiano").tag("it")
                    Text("English").tag("en")
                }
                .pickerStyle(.segmented)
                .onChange(of: language) { _, val in SpecolaSettings.language = val }

                Stepper("Ultime \(hours) ore", value: $hours, in: 6...72)
                    .onChange(of: hours) { _, val in SpecolaSettings.hours = val }
            }
            Section("Modello LLM") {
                Picker("Provider", selection: $llmProvider) {
                    Text("Claude Code CLI").tag("claude")
                    Text("OpenAI").tag("openai")
                    Text("LM Studio (locale)").tag("lmstudio")
                }
                .onChange(of: llmProvider) { _, val in SpecolaSettings.llmProvider = val }

                switch llmProvider {
                case "claude":
                    TextField("Path CLI (auto-detected se vuoto)", text: $claudePath)
                        .onChange(of: claudePath) { _, val in SpecolaSettings.claudePath = val }
                    Text("Posizioni controllate: /usr/local/bin/claude, ~/.local/bin/claude, ~/.claude/local/claude")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                case "openai":
                    SecureField("API Key", text: $openaiApiKey)
                        .onChange(of: openaiApiKey) { _, val in SpecolaSettings.openaiApiKey = val }
                    TextField("Modello", text: $openaiModel)
                        .onChange(of: openaiModel) { _, val in SpecolaSettings.openaiModel = val }
                    Text("Default: gpt-4o. Supporta qualsiasi modello OpenAI chat completions.")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                case "lmstudio":
                    TextField("Endpoint", text: $lmstudioEndpoint)
                        .onChange(of: lmstudioEndpoint) { _, val in SpecolaSettings.lmstudioEndpoint = val }
                    TextField("Modello (opzionale)", text: $lmstudioModel)
                        .onChange(of: lmstudioModel) { _, val in SpecolaSettings.lmstudioModel = val }
                    Text("LM Studio deve essere avviato con il server locale attivo. Default: http://localhost:1234/v1/chat/completions")
                        .font(.caption)
                        .foregroundStyle(.secondary)

                default:
                    EmptyView()
                }
            }
        }
        .formStyle(.grouped)
    }
}
